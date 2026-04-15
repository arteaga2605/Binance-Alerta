"""
Sistema de seguimiento de rendimiento para alertas de trading.
Utiliza SQLite para almacenar el historial y evaluar resultados.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import config


class PerformanceTracker:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_FILE
        self._init_db()

    def _init_db(self):
        """Crea las tablas si no existen."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    analyst TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    entry_time TIMESTAMP NOT NULL,
                    potential_move REAL,
                    target_price REAL,
                    status TEXT DEFAULT 'pending',
                    exit_price REAL,
                    exit_time TIMESTAMP,
                    profit_percent REAL,
                    is_correct INTEGER,
                    evaluated_time TIMESTAMP,
                    metadata TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON alerts(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analyst ON alerts(analyst)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON alerts(status)")

    def register_alert(self, alert_data: Dict) -> str:
        """
        Registra una nueva alerta en la base de datos.
        Retorna el alert_id generado.
        """
        alert_id = f"{alert_data['analyst']}_{alert_data['symbol']}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        entry_price = alert_data['current_price']
        potential = alert_data.get('potential_move_percent')
        if potential is not None:
            target_price = entry_price * (1 + potential / 100)
        else:
            target_price = None

        metadata = {
            'level': alert_data.get('level'),
            'level_type': alert_data.get('level_type'),
            'origin': alert_data.get('origin'),
            'macd_value': alert_data.get('macd_value'),
            'signal_value': alert_data.get('signal_value'),
            'histogram': alert_data.get('histogram'),
            'analysis_timeframe': alert_data.get('analysis_timeframe')
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alerts 
                (alert_id, symbol, analyst, signal_type, entry_price, entry_time, 
                 potential_move, target_price, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                alert_data['symbol'],
                alert_data.get('analyst', 'Unknown'),
                self._get_signal_type_str(alert_data),
                entry_price,
                datetime.now().isoformat(),
                potential,
                target_price,
                'pending',
                json.dumps(metadata)
            ))
        return alert_id

    def _get_signal_type_str(self, alert_data: Dict) -> str:
        """Obtiene una cadena descriptiva del tipo de señal."""
        if alert_data.get('level_type'):
            return alert_data['level_type']  # SOPORTE / RESISTENCIA
        elif alert_data.get('signal_type'):
            return alert_data['signal_type']  # bullish / bearish
        return 'unknown'

    def evaluate_pending_alerts(self, binance_client) -> int:
        """
        Evalúa todas las alertas pendientes que hayan superado el plazo de evaluación.
        Retorna el número de alertas evaluadas.
        """
        cutoff_time = datetime.now() - timedelta(hours=config.EVALUATION_HOURS)
        evaluated_count = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, alert_id, symbol, analyst, signal_type, entry_price, entry_time
                FROM alerts 
                WHERE status = 'pending' AND entry_time <= ?
            """, (cutoff_time.isoformat(),))

            rows = cursor.fetchall()
            for row in rows:
                alert_id = row[1]
                symbol = row[2]
                analyst = row[3]
                signal_type = row[4]
                entry_price = row[5]
                entry_time = datetime.fromisoformat(row[6])

                # Obtener precio actual
                current_price = binance_client.get_current_price(symbol)
                if current_price is None:
                    continue

                # Determinar si fue acierto
                is_correct, profit_percent = self._evaluate_signal(
                    signal_type, entry_price, current_price
                )

                # Actualizar registro
                conn.execute("""
                    UPDATE alerts 
                    SET status = 'evaluated',
                        exit_price = ?,
                        exit_time = ?,
                        profit_percent = ?,
                        is_correct = ?,
                        evaluated_time = ?
                    WHERE alert_id = ?
                """, (
                    current_price,
                    datetime.now().isoformat(),
                    profit_percent,
                    1 if is_correct else 0,
                    datetime.now().isoformat(),
                    alert_id
                ))
                evaluated_count += 1

        return evaluated_count

    def _evaluate_signal(self, signal_type: str, entry_price: float, current_price: float) -> Tuple[bool, float]:
        """Evalúa si la señal fue correcta basado en el movimiento del precio."""
        profit_percent = ((current_price - entry_price) / entry_price) * 100

        # Para S/R: SOPORTE => esperamos subida (profit > umbral positivo)
        #           RESISTENCIA => esperamos bajada (profit < umbral negativo)
        # Para MACD: bullish => profit > umbral positivo
        #            bearish => profit < umbral negativo
        threshold = config.MIN_MOVE_THRESHOLD_PERCENT

        if signal_type in ('SOPORTE', 'bullish'):
            is_correct = profit_percent >= threshold
        else:  # RESISTENCIA, bearish
            is_correct = profit_percent <= -threshold

        return is_correct, profit_percent

    def get_performance_summary(self) -> Dict:
        """Obtiene un resumen de rendimiento por analista."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    analyst,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as incorrect,
                    AVG(profit_percent) as avg_profit,
                    SUM(profit_percent) as total_profit
                FROM alerts
                WHERE status = 'evaluated'
                GROUP BY analyst
            """)
            rows = cursor.fetchall()

        summary = {}
        for row in rows:
            analyst = row[0]
            total = row[1]
            correct = row[2] or 0
            incorrect = row[3] or 0
            accuracy = (correct / total * 100) if total > 0 else 0
            avg_profit = row[4] or 0
            total_profit = row[5] or 0

            summary[analyst] = {
                'total': total,
                'correct': correct,
                'incorrect': incorrect,
                'accuracy': accuracy,
                'avg_profit': avg_profit,
                'total_profit': total_profit
            }
        return summary

    def get_all_evaluated_alerts(self, analyst: Optional[str] = None) -> List[Dict]:
        """Obtiene todas las alertas evaluadas (opcionalmente filtradas por analista)."""
        with sqlite3.connect(self.db_path) as conn:
            if analyst:
                cursor = conn.execute("""
                    SELECT * FROM alerts WHERE status = 'evaluated' AND analyst = ?
                    ORDER BY entry_time DESC
                """, (analyst,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM alerts WHERE status = 'evaluated'
                    ORDER BY entry_time DESC
                """)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
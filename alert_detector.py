"""
Detector de alertas cuando el precio toca soportes o resistencias
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import config


class AlertDetector:
    """Detector de alertas de trading con persistencia de cooldown"""

    def __init__(self, margin_percent: float = None):
        self.margin_percent = margin_percent or config.MARGIN_PERCENTAGE
        self.cooldown_hours = getattr(config, 'ALERT_COOLDOWN_HOURS', 4)
        self.cooldown_file = getattr(config, 'COOLDOWN_FILE', 'alert_cooldown.json')
        self.last_alerts = self._load_cooldown()

    def _load_cooldown(self) -> Dict[str, str]:
        """Carga el registro de últimas alertas desde el archivo JSON."""
        if not os.path.exists(self.cooldown_file):
            return {}
        try:
            with open(self.cooldown_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error cargando archivo de cooldown: {e}. Se usará diccionario vacío.")
            return {}

    def _save_cooldown(self):
        """Guarda el registro de últimas alertas en el archivo JSON."""
        try:
            with open(self.cooldown_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_alerts, f, indent=2)
        except IOError as e:
            print(f"⚠️ Error guardando archivo de cooldown: {e}")

    def is_near_level(self, current_price: float, level: float) -> bool:
        """Verifica si el precio está cerca de un nivel (dentro del margen %)."""
        if level <= 0:
            return False
        diff_percent = abs(current_price - level) / level * 100
        return diff_percent <= self.margin_percent

    def find_near_levels(self, current_price: float,
                         levels: List[float]) -> List[Tuple[float, str, float]]:
        """
        Encuentra niveles cercanos al precio actual.
        Retorna lista de tuplas: (nivel, tipo, diferencia_porcentual)
        """
        near_levels = []
        for level in levels:
            if self.is_near_level(current_price, level):
                if level < current_price:
                    level_type = "SOPORTE"
                else:
                    level_type = "RESISTENCIA"
                diff = ((current_price - level) / level) * 100
                near_levels.append((level, level_type, diff))
        return near_levels

    def _estimate_potential_move(self, current_price: float, level: float,
                                 level_type: str, sr_levels: Dict) -> Optional[float]:
        """
        Estima el movimiento potencial en porcentaje basado en el siguiente nivel significativo.
        - Si está en RESISTENCIA: busca el soporte más cercano por debajo.
        - Si está en SOPORTE: busca la resistencia más cercana por encima.
        Retorna el porcentaje de cambio (positivo si es alcista, negativo si es bajista).
        """
        if level_type == "RESISTENCIA":
            # Buscar el soporte más cercano que esté por debajo del precio actual
            supports = sr_levels.get('supports', [])
            # Filtrar soportes por debajo del precio actual (o nivel)
            valid_supports = [s for s in supports if s < current_price]
            if valid_supports:
                # El más cercano (el mayor de los que están por debajo)
                next_level = max(valid_supports)
                move_percent = ((next_level - current_price) / current_price) * 100
                return move_percent  # Será negativo (bajista)
        else:  # SOPORTE
            # Buscar la resistencia más cercana por encima del precio actual
            resistances = sr_levels.get('resistances', [])
            valid_resistances = [r for r in resistances if r > current_price]
            if valid_resistances:
                # La más cercana (la menor de las que están por encima)
                next_level = min(valid_resistances)
                move_percent = ((next_level - current_price) / current_price) * 100
                return move_percent  # Será positivo (alcista)
        return None

    def check_coin_alerts(self, symbol: str, current_price: float,
                          sr_levels: Dict) -> List[Dict]:
        """
        Verifica alertas para una moneda específica.
        Retorna UNA alerta por moneda (la más cercana) si no está en cooldown.
        """
        alerts = []

        if current_price is None:
            return alerts

        all_levels = sr_levels.get('supports', []) + sr_levels.get('resistances', [])

        near_levels = self.find_near_levels(current_price, all_levels)

        if not near_levels:
            return alerts

        # Seleccionar el nivel más cercano (menor diferencia absoluta)
        best = min(near_levels, key=lambda x: abs(x[2]))
        best_level, best_type, best_diff = best

        # Determinar origen del nivel (semanal o mensual)
        origin = []
        if best_level in sr_levels.get('weekly', {}).get('support', []):
            origin.append('Soporte Semanal')
        if best_level in sr_levels.get('weekly', {}).get('resistance', []):
            origin.append('Resistencia Semanal')
        if best_level in sr_levels.get('monthly', {}).get('support', []):
            origin.append('Soporte Mensual')
        if best_level in sr_levels.get('monthly', {}).get('resistance', []):
            origin.append('Resistencia Mensual')

        origin_str = ' / '.join(origin) if origin else best_type

        # Estimar movimiento potencial
        potential_move = self._estimate_potential_move(
            current_price, best_level, best_type, sr_levels
        )

        alert = {
            'symbol': symbol,
            'current_price': current_price,
            'level': best_level,
            'level_type': best_type,
            'origin': origin_str,
            'diff_percent': best_diff,
            'potential_move_percent': potential_move,
            'timestamp': datetime.now(),
            'analyst': 'S/R'
        }

        # Verificar cooldown
        if self.should_send_alert(symbol):
            alerts.append(alert)
            self.last_alerts[symbol] = datetime.now().isoformat()
            self._save_cooldown()

        return alerts

    def should_send_alert(self, symbol: str) -> bool:
        """Verifica si se debe enviar una alerta para un símbolo."""
        if symbol not in self.last_alerts:
            return True
        last_time_str = self.last_alerts[symbol]
        try:
            last_time = datetime.fromisoformat(last_time_str)
        except ValueError:
            return True
        cooldown_delta = timedelta(hours=self.cooldown_hours)
        return (datetime.now() - last_time) >= cooldown_delta

    def analyze_all_coins(self, prices: Dict[str, float],
                          sr_data: Dict[str, Dict]) -> List[Dict]:
        """Analiza todas las monedas y retorna alertas."""
        all_alerts = []

        # BTC primero
        if config.BTC_SYMBOL in prices and config.BTC_SYMBOL in sr_data:
            btc_price = prices[config.BTC_SYMBOL]
            btc_levels = sr_data[config.BTC_SYMBOL]
            btc_alerts = self.check_coin_alerts(
                config.BTC_SYMBOL, btc_price, btc_levels
            )
            for alert in btc_alerts:
                alert['priority'] = 'HIGH'
                alert['is_btc'] = True
            all_alerts.extend(btc_alerts)

        # Altcoins
        for symbol, price in prices.items():
            if symbol == config.BTC_SYMBOL:
                continue
            if symbol in sr_data:
                alerts = self.check_coin_alerts(symbol, price, sr_data[symbol])
                for alert in alerts:
                    alert['priority'] = 'NORMAL'
                    alert['is_btc'] = False
                all_alerts.extend(alerts)

        return all_alerts
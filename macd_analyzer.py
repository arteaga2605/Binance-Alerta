"""
Analista basado exclusivamente en el indicador MACD.
Detecta cruces de la línea MACD con la línea de señal y genera alertas.
"""

import json
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import config


class MACDAnalyzer:
    """Analista técnico que utiliza el indicador MACD para generar señales."""

    def __init__(self, binance_client):
        self.client = binance_client
        self.fast = config.MACD_FAST
        self.slow = config.MACD_SLOW
        self.signal_period = config.MACD_SIGNAL
        self.analysis_tf = config.MACD_ANALYSIS_TIMEFRAME
        self.cooldown_hours = config.MACD_COOLDOWN_HOURS
        self.cooldown_file = config.MACD_COOLDOWN_FILE
        self.last_alerts = self._load_cooldown()

    def _load_cooldown(self) -> Dict[str, str]:
        """Carga el registro de últimas alertas MACD desde JSON."""
        if not os.path.exists(self.cooldown_file):
            return {}
        try:
            with open(self.cooldown_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_cooldown(self):
        """Guarda el registro de cooldown MACD."""
        try:
            with open(self.cooldown_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_alerts, f, indent=2)
        except IOError:
            pass

    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula MACD, línea de señal e histograma.
        Retorna DataFrame con columnas: macd, signal, histogram.
        """
        if df.empty or len(df) < self.slow + self.signal_period:
            return pd.DataFrame()

        close = df['close']
        ema_fast = close.ewm(span=self.fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        result = pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }, index=df.index)
        return result

    def detect_cross(self, macd_df: pd.DataFrame) -> Optional[str]:
        """
        Detecta el último cruce entre MACD y señal.
        Retorna 'bullish' (macd cruza arriba), 'bearish' (cruza abajo) o None.
        """
        if macd_df.empty or len(macd_df) < 2:
            return None

        macd = macd_df['macd'].values
        signal = macd_df['signal'].values

        prev_macd = macd[-2]
        prev_signal = signal[-2]
        curr_macd = macd[-1]
        curr_signal = signal[-1]

        if prev_macd <= prev_signal and curr_macd > curr_signal:
            return 'bullish'
        elif prev_macd >= prev_signal and curr_macd < curr_signal:
            return 'bearish'
        return None

    def should_send_alert(self, symbol: str) -> bool:
        """Verifica cooldown para MACD."""
        if symbol not in self.last_alerts:
            return True
        last_time_str = self.last_alerts[symbol]
        try:
            last_time = datetime.fromisoformat(last_time_str)
        except ValueError:
            return True
        cooldown_delta = timedelta(hours=self.cooldown_hours)
        return (datetime.now() - last_time) >= cooldown_delta

    def update_cooldown(self, symbol: str):
        """Actualiza la marca de tiempo de la última alerta MACD para un símbolo."""
        self.last_alerts[symbol] = datetime.now().isoformat()
        self._save_cooldown()

    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Analiza un símbolo usando MACD en la temporalidad configurada.
        Retorna un diccionario con la alerta si hay señal y pasa el cooldown.
        """
        # Obtener datos históricos (más días para asegurar suficientes velas)
        lookback = max(60, (self.slow + self.signal_period) * 2)
        df = self.client.get_historical_klines(symbol, self.analysis_tf, lookback_days=lookback)

        if df.empty or len(df) < self.slow + self.signal_period:
            return None

        macd_df = self.calculate_macd(df)
        if macd_df.empty:
            return None

        cross = self.detect_cross(macd_df)
        if not cross:
            return None

        # Verificar cooldown
        if not self.should_send_alert(symbol):
            return None

        current_price = df['close'].iloc[-1]
        macd_val = macd_df['macd'].iloc[-1]
        signal_val = macd_df['signal'].iloc[-1]
        histogram = macd_df['histogram'].iloc[-1]

        # Crear alerta
        alert = {
            'symbol': symbol,
            'current_price': current_price,
            'signal_type': cross,  # 'bullish' o 'bearish'
            'macd_value': macd_val,
            'signal_value': signal_val,
            'histogram': histogram,
            'analysis_timeframe': self.analysis_tf,
            'timestamp': datetime.now(),
            'analyst': 'MACD'
        }

        # Actualizar cooldown
        self.update_cooldown(symbol)
        return alert

    def analyze_multiple(self, symbols: List[str]) -> List[Dict]:
        """
        Analiza una lista de símbolos y retorna todas las alertas generadas.
        """
        alerts = []
        for symbol in symbols:
            alert = self.analyze_symbol(symbol)
            if alert:
                # Marcar si es BTC para prioridad
                alert['is_btc'] = (symbol == config.BTC_SYMBOL)
                alert['priority'] = 'HIGH' if alert['is_btc'] else 'NORMAL'
                alerts.append(alert)
        return alerts
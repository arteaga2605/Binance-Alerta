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
        """
        Carga el registro de últimas alertas desde el archivo JSON.
        Retorna un diccionario con clave = symbol, valor = timestamp ISO.
        """
        if not os.path.exists(self.cooldown_file):
            return {}
        try:
            with open(self.cooldown_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convertir timestamps de string a datetime para uso interno (no es necesario, solo almacenamos string)
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error cargando archivo de cooldown: {e}. Se usará diccionario vacío.")
            return {}

    def _save_cooldown(self):
        """
        Guarda el registro de últimas alertas en el archivo JSON.
        """
        try:
            with open(self.cooldown_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_alerts, f, indent=2)
        except IOError as e:
            print(f"⚠️ Error guardando archivo de cooldown: {e}")

    def is_near_level(self, current_price: float, level: float) -> bool:
        """
        Verifica si el precio está cerca de un nivel (dentro del margen %)
        """
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
                # Determinar si es soporte o resistencia basado en el precio
                if level < current_price:
                    level_type = "SOPORTE"
                else:
                    level_type = "RESISTENCIA"
                diff = ((current_price - level) / level) * 100
                near_levels.append((level, level_type, diff))
        return near_levels

    def check_coin_alerts(self, symbol: str, current_price: float,
                          sr_levels: Dict) -> List[Dict]:
        """
        Verifica alertas para una moneda específica.
        Ahora solo retorna UNA alerta por moneda (la más cercana) si no está en cooldown.
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

        alert = {
            'symbol': symbol,
            'current_price': current_price,
            'level': best_level,
            'level_type': best_type,
            'origin': origin_str,
            'diff_percent': best_diff,
            'timestamp': datetime.now()
        }

        # Verificar si debemos enviar esta alerta (control de cooldown)
        if self.should_send_alert(symbol):
            alerts.append(alert)
            # Actualizar el tiempo de la última alerta para esta moneda
            self.last_alerts[symbol] = datetime.now().isoformat()
            self._save_cooldown()

        return alerts

    def should_send_alert(self, symbol: str) -> bool:
        """
        Verifica si se debe enviar una alerta para un símbolo.
        Retorna True si no hay alerta previa o si ha pasado el cooldown.
        """
        if symbol not in self.last_alerts:
            return True

        last_time_str = self.last_alerts[symbol]
        try:
            last_time = datetime.fromisoformat(last_time_str)
        except ValueError:
            # Si el formato no es válido, asumir que nunca se envió
            return True

        cooldown_delta = timedelta(hours=self.cooldown_hours)
        return (datetime.now() - last_time) >= cooldown_delta

    def analyze_all_coins(self, prices: Dict[str, float],
                          sr_data: Dict[str, Dict]) -> List[Dict]:
        """
        Analiza todas las monedas y retorna alertas (máximo una por moneda, con cooldown)
        """
        all_alerts = []

        # Primero analizar BTC (prioridad)
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

        # Luego analizar altcoins
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
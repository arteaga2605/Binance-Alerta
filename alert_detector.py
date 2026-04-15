"""
Detector de alertas cuando el precio toca soportes o resistencias
"""

from typing import Dict, List, Tuple, Optional
import config


class AlertDetector:
    """Detector de alertas de trading"""

    def __init__(self, margin_percent: float = None):
        self.margin_percent = margin_percent or config.MARGIN_PERCENTAGE
        self.last_alerts = {}  # Para evitar alertas repetitivas

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
        Ahora solo retorna UNA alerta por moneda (la más cercana).
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
            'timestamp': None
        }

        # Evitar alertas duplicadas en corto tiempo
        alert_key = f"{symbol}_{best_level}_{best_type}"
        if self.should_send_alert(alert_key):
            alerts.append(alert)
            self.last_alerts[alert_key] = current_price

        return alerts

    def should_send_alert(self, alert_key: str) -> bool:
        """
        Verifica si se debe enviar una alerta (evita spam)
        """
        if alert_key not in self.last_alerts:
            return True
        return True

    def analyze_all_coins(self, prices: Dict[str, float],
                          sr_data: Dict[str, Dict]) -> List[Dict]:
        """
        Analiza todas las monedas y retorna alertas (máximo una por moneda)
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
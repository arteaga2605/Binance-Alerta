"""
Notificador de Telegram para enviar alertas
"""

import requests
from typing import List, Dict
from datetime import datetime
import config
from coin_names import get_full_name


class TelegramNotifier:
    """Clase para enviar notificaciones a Telegram"""

    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Envía un mensaje a Telegram
        """
        if not self.token or self.token == "TU_TOKEN_DE_BOT_AQUI":
            print("⚠️ Token de Telegram no configurado. Mensaje no enviado.")
            print(f"[SIMULACIÓN] {text}")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error enviando mensaje a Telegram: {e}")
            return False

    def format_alert_message(self, alerts: List[Dict]) -> str:
        """
        Formatea las alertas para enviar a Telegram
        """
        if not alerts:
            return ""

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Separar alertas de BTC (prioridad) y altcoins
        btc_alerts = [a for a in alerts if a.get('is_btc', False)]
        other_alerts = [a for a in alerts if not a.get('is_btc', False)]

        lines = [
            "🚨 <b>ALERTAS DE TRADING</b> 🚨",
            f"📅 {now}",
            "═" * 30
        ]

        # Alertas de BTC primero (prioridad)
        if btc_alerts:
            lines.append("")
            lines.append("🔥 <b>⚠️ ALERTA PRIORITARIA - BITCOIN ⚠️</b> 🔥")
            lines.append("")
            for alert in btc_alerts:
                lines.append(self._format_single_alert(alert))
            lines.append("")
            lines.append("💡 <i>Recuerda: cuando BTC se mueve, las altcoins lo siguen</i>")

        # Alertas de altcoins
        if other_alerts:
            if btc_alerts:
                lines.append("")
                lines.append("─" * 30)
            lines.append("")
            lines.append("📊 <b>ALTCOINS EN NIVELES CLAVE</b>")
            lines.append("")
            for alert in other_alerts:
                lines.append(self._format_single_alert(alert))

        lines.append("")
        lines.append("═" * 30)
        lines.append(f"🤖 <i>Bot: {config.TELEGRAM_BOT_NAME}</i>")

        return "\n".join(lines)

    def _format_single_alert(self, alert: Dict) -> str:
        """Formatea una alerta individual"""
        symbol = alert['symbol']
        full_name = get_full_name(symbol)
        price = alert['current_price']
        level = alert['level']
        diff = alert['diff_percent']

        emoji = "🔴" if alert['level_type'] == "RESISTENCIA" else "🟢"
        direction = "▲" if diff > 0 else "▼"

        lines = [
            f"{emoji} <b>{full_name}</b> ({symbol.replace('USDT', '')}) {emoji}",
            f"   💰 Precio actual: <code>${price:.8f}</code>",
            f"   📍 Nivel ({alert['level_type']}): <code>${level:.8f}</code>",
            f"   📈 Diferencia: {direction} {abs(diff):.2f}%",
            f"   🏷️ Origen: {alert['origin']}"
        ]
        return "\n".join(lines)

    def send_alerts(self, alerts: List[Dict]) -> bool:
        """
        Envía todas las alertas formateadas a Telegram
        """
        if not alerts:
            print("✅ No hay alertas para enviar.")
            return True

        message = self.format_alert_message(alerts)
        return self.send_message(message)

    def send_status_update(self, coins_analyzed: int,
                           total_alerts: int) -> bool:
        """
        Envía un mensaje de estado del sistema
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        text = f"""
🤖 <b>SISTEMA DE ALERTAS - ESTADO</b>
📅 {now}
════════════════════════════
📊 Monedas analizadas: <b>{coins_analyzed}</b>
🚨 Alertas detectadas: <b>{total_alerts}</b>
────────────────────────────
⏱️ Próximo análisis en 5 minutos
        """
        return self.send_message(text.strip())
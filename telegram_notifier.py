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

    def format_combined_message(self, sr_alerts: List[Dict], macd_alerts: List[Dict]) -> str:
        """
        Formatea las alertas de ambos analistas en un solo mensaje.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "🚨 <b>ALERTAS DE TRADING v2.0</b> 🚨",
            f"📅 {now}",
            "═" * 35
        ]

        # Sección S/R
        lines.append("")
        lines.append("📊 <b>ANÁLISIS DE SOPORTE/RESISTENCIA</b>")
        lines.append("─" * 35)
        if sr_alerts:
            btc_sr = [a for a in sr_alerts if a.get('is_btc', False)]
            other_sr = [a for a in sr_alerts if not a.get('is_btc', False)]
            if btc_sr:
                lines.append("🔥 <b>BITCOIN (PRIORITARIO)</b>")
                for alert in btc_sr:
                    lines.append(self._format_sr_alert(alert))
            if other_sr:
                if btc_sr:
                    lines.append("")
                for alert in other_sr:
                    lines.append(self._format_sr_alert(alert))
        else:
            lines.append("✅ Sin señales S/R en este ciclo.")

        # Sección MACD
        lines.append("")
        lines.append("📈 <b>ANÁLISIS MACD</b>")
        lines.append("─" * 35)
        if macd_alerts:
            btc_macd = [a for a in macd_alerts if a.get('is_btc', False)]
            other_macd = [a for a in macd_alerts if not a.get('is_btc', False)]
            if btc_macd:
                lines.append("🔥 <b>BITCOIN (PRIORITARIO)</b>")
                for alert in btc_macd:
                    lines.append(self._format_macd_alert(alert))
            if other_macd:
                if btc_macd:
                    lines.append("")
                for alert in other_macd:
                    lines.append(self._format_macd_alert(alert))
        else:
            lines.append("✅ Sin señales MACD en este ciclo.")

        lines.append("")
        lines.append("═" * 35)
        lines.append(f"🤖 <i>Bot: {config.TELEGRAM_BOT_NAME} (v2.0)</i>")

        return "\n".join(lines)

    def _format_sr_alert(self, alert: Dict) -> str:
        """Formatea una alerta de S/R."""
        symbol = alert['symbol']
        full_name = get_full_name(symbol)
        price = alert['current_price']
        level = alert['level']
        diff = alert['diff_percent']
        emoji = "🔴" if alert['level_type'] == "RESISTENCIA" else "🟢"
        direction = "▲" if diff > 0 else "▼"

        return (
            f"{emoji} <b>{full_name}</b> ({symbol.replace('USDT', '')})\n"
            f"   💰 Precio: ${price:.8f}\n"
            f"   📍 Nivel ({alert['level_type']}): ${level:.8f}\n"
            f"   📈 Diferencia: {direction} {abs(diff):.2f}%\n"
            f"   🏷️ Origen: {alert['origin']}"
        )

    def _format_macd_alert(self, alert: Dict) -> str:
        """Formatea una alerta MACD."""
        symbol = alert['symbol']
        full_name = get_full_name(symbol)
        price = alert['current_price']
        signal_type = alert['signal_type']
        macd_val = alert['macd_value']
        signal_val = alert['signal_value']
        hist = alert['histogram']

        if signal_type == 'bullish':
            emoji = "📈🐂"
            text_signal = "CRUCE ALCISTA (MACD > Señal)"
        else:
            emoji = "📉🐻"
            text_signal = "CRUCE BAJISTA (MACD < Señal)"

        return (
            f"{emoji} <b>{full_name}</b> ({symbol.replace('USDT', '')})\n"
            f"   💰 Precio: ${price:.8f}\n"
            f"   📊 MACD: {macd_val:.8f} | Señal: {signal_val:.8f}\n"
            f"   📉 Histograma: {hist:.8f}\n"
            f"   ⏱️ Temporalidad análisis: {alert['analysis_timeframe']}\n"
            f"   🏷️ Señal: {text_signal}"
        )

    def send_combined_alerts(self, sr_alerts: List[Dict], macd_alerts: List[Dict]) -> bool:
        """
        Envía todas las alertas (S/R y MACD) en un solo mensaje estructurado.
        """
        if not sr_alerts and not macd_alerts:
            print("✅ No hay alertas para enviar.")
            return True

        message = self.format_combined_message(sr_alerts, macd_alerts)
        return self.send_message(message)

    def send_alerts(self, alerts: List[Dict]) -> bool:
        """
        Método legacy (compatibilidad). Se recomienda usar send_combined_alerts.
        """
        if not alerts:
            return True
        # Distinguir por campo 'analyst' para mantener compatibilidad
        sr = [a for a in alerts if a.get('analyst') == 'S/R']
        macd = [a for a in alerts if a.get('analyst') == 'MACD']
        return self.send_combined_alerts(sr, macd)

    def send_status_update(self, coins_analyzed: int, total_alerts: int) -> bool:
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
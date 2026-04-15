"""
Configuración del sistema de alertas de trading
"""

import os

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = "7897536624:AAHHofbqCGckXmOCjnlt8oQ0EKS5hiGfIpE"
TELEGRAM_CHAT_ID = "1551875559"
TELEGRAM_BOT_NAME = "WonderS"

# Configuración de trading (común)
MARGIN_PERCENTAGE = 1.0
TIMEFRAME_ENTRY = "4h"
LOW_CAP_VOLUME_THRESHOLD = 50_000_000
NUM_COINS_TO_MONITOR = 50
BTC_SYMBOL = "BTCUSDT"

COINS_PER_ECOSYSTEM = 7

# Control de alertas repetitivas (S/R)
ALERT_COOLDOWN_HOURS = 4
COOLDOWN_FILE = os.path.join(os.path.dirname(__file__), "alert_cooldown.json")

# Configuración MACD
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MACD_ANALYSIS_TIMEFRAME = "1d"
MACD_COOLDOWN_HOURS = 6
MACD_COOLDOWN_FILE = os.path.join(os.path.dirname(__file__), "alert_cooldown_macd.json")
MACD_ATR_PERIOD = 14
MACD_ATR_MULTIPLIER = 1.5

# Configuración de evaluación de rendimiento
EVALUATION_HOURS = 24                # Plazo para evaluar una alerta (horas)
MIN_MOVE_THRESHOLD_PERCENT = 0.5     # Movimiento mínimo para considerar acierto (%)
DATABASE_FILE = os.path.join(os.path.dirname(__file__), "alerts_history.db")
REPORT_IMAGE_FILE = os.path.join(os.path.dirname(__file__), "analysts_performance.png")

# Intervalos de tiempo S/R
SR_PERIODS = {
    "1_week": "1w",
    "1_month": "1M"
}

# Pares excluidos
EXCLUDED_SYMBOLS = [
    "USDCUSDT", "BUSDUSDT", "DAIUSDT", "USDPUSDT", "TUSDUSDT",
    "USDCBUSD", "USDCUSDC", "EURUSDT", "GBPUSDT"
]
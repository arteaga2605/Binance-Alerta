"""
Configuración del sistema de alertas de trading
"""

import os

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = "7897536624:AAHHofbqCGckXmOCjnlt8oQ0EKS5hiGfIpE"  # Token real del bot WonderS
TELEGRAM_CHAT_ID = "1551875559"                                      # Tu ID de Telegram
TELEGRAM_BOT_NAME = "WonderS"

# Configuración de trading (común)
MARGIN_PERCENTAGE = 1.0          # Margen de sensibilidad del 1%
TIMEFRAME_ENTRY = "4h"           # Temporalidad para las operaciones
LOW_CAP_VOLUME_THRESHOLD = 50_000_000  # Volumen máximo 24h en USDT (50M) para incluir más monedas
NUM_COINS_TO_MONITOR = 50        # Ahora analiza al menos 50 monedas
BTC_SYMBOL = "BTCUSDT"           # Par de Bitcoin a monitorear con prioridad

# Diversificación por ecosistemas (se calculará dinámicamente según el total)
COINS_PER_ECOSYSTEM = 7          # Valor orientativo; el sistema lo ajustará automáticamente

# Control de alertas repetitivas (para S/R)
ALERT_COOLDOWN_HOURS = 4
COOLDOWN_FILE = os.path.join(os.path.dirname(__file__), "alert_cooldown.json")

# Configuración del analista MACD
MACD_FAST = 12                   # Período rápido EMA
MACD_SLOW = 26                   # Período lento EMA
MACD_SIGNAL = 9                  # Período de la señal EMA
MACD_ANALYSIS_TIMEFRAME = "1d"   # Temporalidad para calcular MACD ("1d" o "1w")
MACD_COOLDOWN_HOURS = 6          # Cooldown independiente para alertas MACD
MACD_COOLDOWN_FILE = os.path.join(os.path.dirname(__file__), "alert_cooldown_macd.json")

# Intervalos de tiempo para soportes/resistencias
SR_PERIODS = {
    "1_week": "1w",    # 1 semana
    "1_month": "1M"    # 1 mes
}

# Pares excluidos (stablecoins, pares no deseados)
EXCLUDED_SYMBOLS = [
    "USDCUSDT", "BUSDUSDT", "DAIUSDT", "USDPUSDT", "TUSDUSDT",
    "USDCBUSD", "USDCUSDC", "EURUSDT", "GBPUSDT"
]
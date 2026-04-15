"""
Configuración del sistema de alertas de trading
"""

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = "7897536624:AAHHofbqCGckXmOCjnlt8oQ0EKS5hiGfIpE"  # Token real del bot WonderS
TELEGRAM_CHAT_ID = "1551875559"                                      # Tu ID de Telegram
TELEGRAM_BOT_NAME = "WonderS"

# Configuración de trading
MARGIN_PERCENTAGE = 1.0          # Margen de sensibilidad del 1%
TIMEFRAME_ENTRY = "4h"           # Temporalidad para las operaciones
LOW_CAP_VOLUME_THRESHOLD = 50_000_000  # Volumen máximo 24h en USDT (50M) para incluir más monedas
NUM_COINS_TO_MONITOR = 50        # Ahora analiza al menos 50 monedas
BTC_SYMBOL = "BTCUSDT"           # Par de Bitcoin a monitorear con prioridad

# Diversificación por ecosistemas (se calculará dinámicamente según el total)
COINS_PER_ECOSYSTEM = 7          # Valor orientativo; el sistema lo ajustará automáticamente

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
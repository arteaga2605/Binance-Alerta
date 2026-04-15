"""
Definición de ecosistemas de criptomonedas para diversificar la selección.
Cada ecosistema contiene una lista de símbolos de Binance (pares USDT).
Se ha ampliado la lista para asegurar al menos 50 monedas seleccionables.
"""

ECOSYSTEMS = {
    "AI": [
        "FETUSDT", "AGIXUSDT", "OCEANUSDT", "NMRUSDT", "CTXCUSDT",
        "MDTUSDT", "RLCUSDT", "DATAUSDT", "VIDTUSDT", "PHBUSDT",
        "NKNUSDT", "ARKMUSDT", "WLDUSDT", "TAOUSDT", "PRIMEUSDT"
    ],
    "DeFi": [
        "UNIUSDT", "AAVEUSDT", "MKRUSDT", "COMPUSDT", "SNXUSDT",
        "CRVUSDT", "SUSHIUSDT", "YFIUSDT", "BALUSDT", "1INCHUSDT",
        "LDOUSDT", "RPLUSDT", "FXSUSDT", "PENDLEUSDT", "RDNTUSDT"
    ],
    "Meme": [
        "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "BONKUSDT",
        "WIFUSDT", "MEMEUSDT", "PEOPLEUSDT", "TURBOUSDT", "BABYDOGEUSDT",
        "COQUSDT", "MYROUSDT", "WENUSDT", "SLERFUSDT", "SAMOUSDT"
    ],
    "Layer1": [
        "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "AVAXUSDT",
        "DOTUSDT", "NEARUSDT", "ATOMUSDT", "FTMUSDT", "ALGOUSDT",
        "ICPUSDT", "HBARUSDT", "EGLDUSDT", "FLOWUSDT", "ROSEUSDT"
    ],
    "Layer2": [
        "MATICUSDT", "ARBUSDT", "OPUSDT", "IMXUSDT", "LRCUSDT",
        "SKLUSDT", "CELRUSDT", "OMGUSDT", "ZKSUSDT", "STRKUSDT",
        "METISUSDT", "BOBAUSDT", "COTIUSDT", "MINAUSDT", "AZEROUSDT"
    ],
    "Gaming": [
        "AXSUSDT", "SANDUSDT", "MANAUSDT", "ENJUSDT", "GALAUSDT",
        "ILVUSDT", "ALICEUSDT", "TLMUSDT", "DARUSDT", "VOXELUSDT",
        "MCUSDT", "PYRUSDT", "YGGUSDT", "BIGTIMEUSDT", "NAKAUSDT"
    ],
    "Oracle": [
        "LINKUSDT", "BANDUSDT", "TRBUSDT", "API3USDT", "UMAUSDT",
        "DIAUSDT", "PYTHUSDT"
    ],
    "Storage": [
        "FILUSDT", "ARUSDT", "STORJUSDT", "SCUSDT", "ANKRUSDT",
        "HOTUSDT", "BLZUSDT"
    ],
    "RWA": [
        "CFGUSDT", "TRUUSDT", "RIOUSDT", "SNXUSDT", "MKRUSDT",
        "ONDOUSDT", "TOKENUSDT"
    ]
}

# Mapeo inverso: símbolo -> ecosistema
SYMBOL_TO_ECOSYSTEM = {}
for eco, symbols in ECOSYSTEMS.items():
    for sym in symbols:
        SYMBOL_TO_ECOSYSTEM[sym] = eco


def get_ecosystem_for_symbol(symbol: str) -> str:
    """Retorna el ecosistema de un símbolo, o 'Other' si no está definido."""
    return SYMBOL_TO_ECOSYSTEM.get(symbol, "Other")
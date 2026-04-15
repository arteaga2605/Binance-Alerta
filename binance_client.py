"""
Cliente para interactuar con la API pública de Binance
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional, Set
from binance.client import Client
from binance.exceptions import BinanceAPIException
import config
from ecosystems import ECOSYSTEMS, get_ecosystem_for_symbol


class BinanceClient:
    """Cliente para la API pública de Binance (no requiere autenticación)"""

    def __init__(self):
        self.client = Client("", "")  # API pública no requiere keys
        self._ticker_cache = None
        self._ticker_cache_time = None
        self._cache_duration = 60  # 1 minuto de caché
        self._spot_symbols_cache = None
        self._futures_symbols_cache = None

    def get_spot_symbols(self) -> Set[str]:
        """
        Obtiene todos los símbolos disponibles en Spot trading.
        """
        if self._spot_symbols_cache is not None:
            return self._spot_symbols_cache

        try:
            exchange_info = self.client.get_exchange_info()
            symbols = set()
            for s in exchange_info['symbols']:
                if s['status'] == 'TRADING':
                    symbols.add(s['symbol'])
            self._spot_symbols_cache = symbols
            return symbols
        except Exception as e:
            print(f"Error obteniendo símbolos Spot: {e}")
            return set()

    def get_futures_symbols(self) -> Set[str]:
        """
        Obtiene todos los símbolos disponibles en Futuros (USDⓈ-M y COIN-M).
        """
        if self._futures_symbols_cache is not None:
            return self._futures_symbols_cache

        symbols = set()
        try:
            # USDⓈ-M Futures
            um_exchange_info = self.client.futures_exchange_info()
            for s in um_exchange_info['symbols']:
                if s.get('status') == 'TRADING':
                    symbols.add(s['symbol'])
        except Exception as e:
            print(f"Error obteniendo símbolos USDⓈ-M Futures: {e}")

        try:
            # COIN-M Futures
            cm_exchange_info = self.client.futures_coin_exchange_info()
            for s in cm_exchange_info['symbols']:
                # En COIN-M el campo es 'contractStatus' en lugar de 'status'
                if s.get('contractStatus') == 'TRADING':
                    symbols.add(s['symbol'])
        except Exception as e:
            print(f"Error obteniendo símbolos COIN-M Futures: {e}")

        self._futures_symbols_cache = symbols
        return symbols

    def get_tradable_symbols(self) -> Set[str]:
        """
        Obtiene la unión de símbolos disponibles en Spot y Futuros.
        """
        spot = self.get_spot_symbols()
        futures = self.get_futures_symbols()
        return spot.union(futures)

    def get_all_usdt_pairs(self) -> List[str]:
        """
        Obtiene todos los pares que terminan en USDT y están disponibles en Spot o Futuros.
        """
        try:
            tradable = self.get_tradable_symbols()
            symbols = []
            for symbol in tradable:
                if symbol.endswith('USDT'):
                    # Excluir stablecoins y pares no deseados
                    if symbol not in config.EXCLUDED_SYMBOLS:
                        symbols.append(symbol)
            return symbols
        except Exception as e:
            print(f"Error obteniendo pares USDT: {e}")
            return []

    def get_24hr_tickers(self, use_cache: bool = True) -> List[Dict]:
        """
        Obtiene estadísticas de 24 horas para todos los pares
        """
        if use_cache and self._ticker_cache and self._ticker_cache_time:
            if time.time() - self._ticker_cache_time < self._cache_duration:
                return self._ticker_cache

        try:
            tickers = self.client.get_ticker()
            self._ticker_cache = tickers
            self._ticker_cache_time = time.time()
            return tickers
        except Exception as e:
            print(f"Error obteniendo tickers 24hr: {e}")
            return self._ticker_cache or []

    def get_low_cap_altcoins(self, limit: int = None) -> List[str]:
        """
        Identifica altcoins de baja/media capitalización basado en volumen 24h,
        diversificando por ecosistemas y garantizando al menos 'limit' monedas.
        Solo incluye monedas disponibles en Spot o Futuros.
        """
        if limit is None:
            limit = config.NUM_COINS_TO_MONITOR

        tickers = self.get_24hr_tickers()
        usdt_pairs = self.get_all_usdt_pairs()
        usdt_set = set(usdt_pairs)

        # Filtrar pares USDT válidos con volumen dentro del umbral
        candidates = []
        for ticker in tickers:
            symbol = ticker['symbol']
            if symbol not in usdt_set:
                continue
            if symbol == config.BTC_SYMBOL:
                continue

            try:
                volume = float(ticker['quoteVolume'])
                last_price = float(ticker['lastPrice'])

                if volume > 0 and volume < config.LOW_CAP_VOLUME_THRESHOLD:
                    eco = get_ecosystem_for_symbol(symbol)
                    candidates.append({
                        'symbol': symbol,
                        'volume': volume,
                        'price': last_price,
                        'change_24h': float(ticker['priceChangePercent']),
                        'ecosystem': eco
                    })
            except (KeyError, ValueError, TypeError):
                continue

        # Agrupar candidatos por ecosistema
        by_ecosystem = {}
        for c in candidates:
            eco = c['ecosystem']
            if eco not in by_ecosystem:
                by_ecosystem[eco] = []
            by_ecosystem[eco].append(c)

        # Ordenar cada grupo por volumen ascendente (menor volumen = más baja cap)
        for eco in by_ecosystem:
            by_ecosystem[eco].sort(key=lambda x: x['volume'])

        # Calcular cuántas monedas tomar por ecosistema para alcanzar el límite
        defined_ecos = list(ECOSYSTEMS.keys())
        num_ecos = len(defined_ecos)
        per_eco_base = max(2, limit // num_ecos)  # Al menos 2 por ecosistema
        extra = limit % num_ecos

        selected = []
        # Primera pasada: tomar 'per_eco_base' monedas de cada ecosistema definido
        for i, eco_name in enumerate(defined_ecos):
            if eco_name not in by_ecosystem:
                continue
            take = per_eco_base
            if i < extra:
                take += 1
            for coin in by_ecosystem[eco_name][:take]:
                selected.append(coin['symbol'])
            # Eliminar para no repetir en la siguiente fase
            by_ecosystem[eco_name] = by_ecosystem[eco_name][take:]

        # Si aún faltan monedas, tomar del ecosistema "Other"
        if len(selected) < limit:
            remaining = []
            for eco, coins in by_ecosystem.items():
                remaining.extend(coins)
            remaining.sort(key=lambda x: x['volume'])
            for coin in remaining:
                if len(selected) >= limit:
                    break
                if coin['symbol'] not in selected:
                    selected.append(coin['symbol'])

        # Si todavía faltan, recurrir a lista de respaldo ampliada
        if len(selected) < limit:
            fallback = self._get_fallback_coins()
            for fb in fallback:
                if fb not in selected and fb != config.BTC_SYMBOL:
                    selected.append(fb)
                    if len(selected) >= limit:
                        break

        return selected[:limit]

    def _get_fallback_coins(self) -> List[str]:
        """Lista de respaldo amplia de altcoins de baja/media capitalización"""
        return [
            "TRUUSDT", "COTIUSDT", "REIUSDT", "DGBUSDT", "DOCKUSDT",
            "FRONTUSDT", "NKNUSDT", "VITEUSDT", "DUSKUSDT", "PERLUSDT",
            "FETUSDT", "AGIXUSDT", "UNIUSDT", "AAVEUSDT", "DOGEUSDT",
            "SHIBUSDT", "PEPEUSDT", "WIFUSDT", "BONKUSDT", "FLOKIUSDT",
            "ARBUSDT", "OPUSDT", "LDOUSDT", "RNDRUSDT", "INJUSDT",
            "STXUSDT", "CFXUSDT", "KASUSDT", "SEIUSDT", "SUIUSDT",
            "APTUSDT", "TIAUSDT", "JTOUSDT", "PYTHUSDT", "JUPUSDT",
            "WUSDT", "ENAUSDT", "ETHFIUSDT", "ALTUSDT", "MANTAUSDT",
            "XAIUSDT", "ACEUSDT", "NFPUSDT", "AIUSDT", "PORTALUSDT"
        ]

    def get_historical_klines(self, symbol: str, interval: str,
                              lookback_days: int = 30) -> pd.DataFrame:
        """
        Obtiene velas históricas para un símbolo
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback_days)

            interval_map = {
                "1w": Client.KLINE_INTERVAL_1WEEK,
                "1M": Client.KLINE_INTERVAL_1MONTH,
                "4h": Client.KLINE_INTERVAL_4HOUR,
                "1h": Client.KLINE_INTERVAL_1HOUR,
                "1d": Client.KLINE_INTERVAL_1DAY
            }

            binance_interval = interval_map.get(interval, Client.KLINE_INTERVAL_1DAY)

            klines = self.client.get_historical_klines(
                symbol, binance_interval,
                start_time.strftime("%d %b %Y %H:%M:%S"),
                end_time.strftime("%d %b %Y %H:%M:%S")
            )

            if not klines:
                return pd.DataFrame()

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df

        except BinanceAPIException as e:
            print(f"Error API Binance para {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error obteniendo klines para {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Obtiene el precio actual de un símbolo
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            print(f"Error obteniendo precio para {symbol}: {e}")
            return None

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Obtiene precios actuales para múltiples símbolos
        """
        prices = {}
        try:
            all_prices = self.client.get_all_tickers()
            price_dict = {p['symbol']: float(p['price']) for p in all_prices}

            for symbol in symbols:
                if symbol in price_dict:
                    prices[symbol] = price_dict[symbol]
        except Exception as e:
            print(f"Error obteniendo precios múltiples: {e}")

        return prices
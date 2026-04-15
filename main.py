#!/usr/bin/env python3
"""
Sistema de Alertas de Trading para Binance
Ejecución principal (manual o programada)
"""

import sys
import time
from datetime import datetime
from typing import List, Dict

from binance_client import BinanceClient
from sr_calculator import SupportResistanceCalculator
from alert_detector import AlertDetector
from macd_analyzer import MACDAnalyzer
from telegram_notifier import TelegramNotifier
import config


class CryptoAlertSystem:
    """Sistema principal de alertas de trading con dos analistas independientes."""

    def __init__(self):
        self.binance = BinanceClient()
        self.sr_calc = SupportResistanceCalculator(order=3)
        self.sr_detector = AlertDetector()
        self.macd_analyzer = MACDAnalyzer(self.binance)
        self.notifier = TelegramNotifier()
        self.monitored_coins = []

    def get_coins_to_monitor(self) -> List[str]:
        """
        Obtiene la lista de monedas a monitorear (BTC + altcoins low cap)
        """
        coins = []
        coins.append(config.BTC_SYMBOL)

        print("📊 Buscando altcoins de baja capitalización...")
        altcoins = self.binance.get_low_cap_altcoins(limit=config.NUM_COINS_TO_MONITOR)

        if not altcoins:
            print("⚠️ No se encontraron altcoins. Usando lista de respaldo.")
            altcoins = self._get_fallback_coins()

        coins.extend(altcoins)
        self.monitored_coins = coins

        print(f"✅ Monedas a monitorear: {len(coins)}")
        print(f"   BTC: {config.BTC_SYMBOL}")
        print(f"   Altcoins ({len(altcoins)}): {', '.join(altcoins[:5])}...")

        return coins

    def _get_fallback_coins(self) -> List[str]:
        """Lista de respaldo de altcoins de baja capitalización"""
        return [
            "TRUUSDT", "COTIUSDT", "REIUSDT", "DGBUSDT", "DOCKUSDT",
            "FRONTUSDT", "NKNUSDT", "VITEUSDT", "DUSKUSDT", "PERLUSDT",
            "FETUSDT", "AGIXUSDT", "UNIUSDT", "AAVEUSDT", "DOGEUSDT"
        ]

    def fetch_historical_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Obtiene datos históricos para calcular soportes y resistencias
        """
        print("\n📈 Obteniendo datos históricos para S/R...")
        sr_data = {}

        for i, symbol in enumerate(symbols, 1):
            print(f"   [{i}/{len(symbols)}] Procesando {symbol}...", end=" ")

            weekly_df = self.binance.get_historical_klines(
                symbol, "1w", lookback_days=90
            )
            monthly_df = self.binance.get_historical_klines(
                symbol, "1M", lookback_days=180
            )

            if weekly_df.empty and monthly_df.empty:
                print("❌ Sin datos")
                continue

            levels = self.sr_calc.get_all_levels(symbol, weekly_df, monthly_df)
            sr_data[symbol] = levels

            num_supports = len(levels.get('supports', []))
            num_resistances = len(levels.get('resistances', []))
            print(f"✅ S:{num_supports} R:{num_resistances}")

        return sr_data

    def fetch_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Obtiene precios actuales de todas las monedas
        """
        print("\n💰 Obteniendo precios actuales...")
        prices = self.binance.get_multiple_prices(symbols)

        for symbol, price in prices.items():
            if price < 1:
                print(f"   {symbol}: ${price:.8f}")
            else:
                print(f"   {symbol}: ${price:.4f}")

        return prices

    def run_sr_analysis(self, coins: List[str]) -> List[Dict]:
        """Ejecuta el análisis de Soportes y Resistencias."""
        print("\n🔍 [ANALISTA S/R] Calculando niveles...")
        sr_data = self.fetch_historical_data(coins)
        symbols_with_data = list(sr_data.keys())
        prices = self.fetch_current_prices(symbols_with_data)

        alerts = self.sr_detector.analyze_all_coins(prices, sr_data)
        for alert in alerts:
            alert['analyst'] = 'S/R'
        return alerts

    def run_macd_analysis(self, coins: List[str]) -> List[Dict]:
        """Ejecuta el análisis MACD."""
        print(f"\n📉 [ANALISTA MACD] Calculando indicadores en {config.MACD_ANALYSIS_TIMEFRAME}...")
        alerts = self.macd_analyzer.analyze_multiple(coins)
        for alert in alerts:
            alert['analyst'] = 'MACD'
        return alerts

    def run_analysis(self) -> Dict[str, List[Dict]]:
        """
        Ejecuta ambos análisis y retorna un diccionario con las alertas de cada analista.
        """
        print("\n" + "="*50)
        print(f"🚀 INICIANDO ANÁLISIS DUAL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)

        coins = self.get_coins_to_monitor()

        # Ejecutar ambos análisis
        sr_alerts = self.run_sr_analysis(coins)
        macd_alerts = self.run_macd_analysis(coins)

        total_alerts = len(sr_alerts) + len(macd_alerts)
        print(f"\n📊 RESUMEN DEL ANÁLISIS:")
        print(f"   Monedas analizadas: {len(coins)}")
        print(f"   Alertas S/R: {len(sr_alerts)}")
        print(f"   Alertas MACD: {len(macd_alerts)}")
        print(f"   Total alertas: {total_alerts}")

        btc_sr = [a for a in sr_alerts if a.get('is_btc', False)]
        btc_macd = [a for a in macd_alerts if a.get('is_btc', False)]
        if btc_sr or btc_macd:
            print(f"\n   🔥 ALERTAS DE BTC: S/R={len(btc_sr)} MACD={len(btc_macd)}")

        return {'sr': sr_alerts, 'macd': macd_alerts}

    def run(self, send_telegram: bool = True):
        """
        Ejecuta el sistema completo
        """
        try:
            alerts_dict = self.run_analysis()
            all_alerts = alerts_dict['sr'] + alerts_dict['macd']

            if send_telegram:
                if all_alerts:
                    print("\n📤 Enviando alertas a Telegram...")
                    self.notifier.send_combined_alerts(alerts_dict['sr'], alerts_dict['macd'])
                else:
                    print("\n✅ No se detectaron alertas.")
                    self.notifier.send_status_update(
                        len(self.monitored_coins), len(all_alerts)
                    )

            print("\n✨ Análisis completado exitosamente!")

        except KeyboardInterrupt:
            print("\n\n⚠️ Ejecución interrumpida por el usuario.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error durante la ejecución: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Función principal"""
    print("""
    ╔══════════════════════════════════════════════╗
    ║   🚀 SISTEMA DE ALERTAS DE TRADING v2.0    ║
    ║   Binance + Telegram (S/R + MACD)           ║
    ╚══════════════════════════════════════════════╝
    """)

    if config.TELEGRAM_BOT_TOKEN == "TU_TOKEN_DE_BOT_AQUI":
        print("⚠️ ADVERTENCIA: Token de Telegram no configurado.")
        print("   Las alertas se mostrarán solo en consola.")
        print("   Edita config.py para agregar tu token.\n")

    system = CryptoAlertSystem()
    system.run(send_telegram=True)


if __name__ == "__main__":
    main()
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
from telegram_notifier import TelegramNotifier
import config


class CryptoAlertSystem:
    """Sistema principal de alertas de trading"""

    def __init__(self):
        self.binance = BinanceClient()
        self.sr_calc = SupportResistanceCalculator(order=3)
        self.detector = AlertDetector()
        self.notifier = TelegramNotifier()

        # Para seguimiento de monedas analizadas
        self.monitored_coins = []

    def get_coins_to_monitor(self) -> List[str]:
        """
        Obtiene la lista de monedas a monitorear (BTC + altcoins low cap)
        """
        coins = []

        # BTC siempre incluido
        coins.append(config.BTC_SYMBOL)

        # Obtener altcoins de baja capitalización
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
            "FRONTUSDT", "NKNUSDT", "VITEUSDT", "DUSKUSDT", "PERLUSDT"
        ]

    def fetch_historical_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Obtiene datos históricos para calcular soportes y resistencias
        """
        print("\n📈 Obteniendo datos históricos...")
        sr_data = {}

        for i, symbol in enumerate(symbols, 1):
            print(f"   [{i}/{len(symbols)}] Procesando {symbol}...", end=" ")

            # Datos semanales
            weekly_df = self.binance.get_historical_klines(
                symbol, "1w", lookback_days=90
            )

            # Datos mensuales
            monthly_df = self.binance.get_historical_klines(
                symbol, "1M", lookback_days=180
            )

            if weekly_df.empty and monthly_df.empty:
                print("❌ Sin datos")
                continue

            # Calcular niveles
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
            print(f"   {symbol}: ${price:.8f}" if price < 1 else f"   {symbol}: ${price:.4f}")

        return prices

    def run_analysis(self) -> List[Dict]:
        """
        Ejecuta el análisis completo y retorna alertas
        """
        print("\n" + "="*50)
        print(f"🚀 INICIANDO ANÁLISIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)

        # 1. Obtener monedas a monitorear
        coins = self.get_coins_to_monitor()

        # 2. Obtener datos históricos y calcular S/R
        sr_data = self.fetch_historical_data(coins)

        # 3. Obtener precios actuales
        symbols_with_data = list(sr_data.keys())
        prices = self.fetch_current_prices(symbols_with_data)

        # 4. Detectar alertas
        print("\n🔍 Detectando niveles cercanos (margen {}%)...".format(
            config.MARGIN_PERCENTAGE
        ))
        alerts = self.detector.analyze_all_coins(prices, sr_data)

        # 5. Mostrar resumen
        print(f"\n📊 RESUMEN DEL ANÁLISIS:")
        print(f"   Monedas analizadas: {len(symbols_with_data)}")
        print(f"   Alertas detectadas: {len(alerts)}")

        btc_alerts = [a for a in alerts if a.get('is_btc', False)]
        if btc_alerts:
            print(f"\n   🔥 ALERTAS DE BTC (PRIORITARIAS): {len(btc_alerts)}")

        return alerts

    def run(self, send_telegram: bool = True):
        """
        Ejecuta el sistema completo
        """
        try:
            alerts = self.run_analysis()

            if send_telegram:
                if alerts:
                    print("\n📤 Enviando alertas a Telegram...")
                    self.notifier.send_alerts(alerts)
                else:
                    print("\n✅ No se detectaron alertas.")
                    # Opcional: enviar mensaje de estado
                    self.notifier.send_status_update(
                        len(self.monitored_coins), len(alerts)
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
    ║   🚀 SISTEMA DE ALERTAS DE TRADING v1.0    ║
    ║   Binance + Telegram                        ║
    ╚══════════════════════════════════════════════╝
    """)

    # Verificar configuración de Telegram
    if config.TELEGRAM_BOT_TOKEN == "7897536624:AAHHofbqCGckXmOCjnlt8oQ0EKS5hiGfIpE":
        print("⚠️ ADVERTENCIA: Token de Telegram no configurado.")
        print("   Las alertas se mostrarán solo en consola.")
        print("   Edita config.py para agregar tu token.\n")

    system = CryptoAlertSystem()
    system.run(send_telegram=True)


if __name__ == "__main__":
    main()
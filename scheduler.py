#!/usr/bin/env python3
"""
Programador para ejecutar el sistema cada 5 minutos
"""

import schedule
import time
import signal
import sys
from datetime import datetime
from main import CryptoAlertSystem


class AlertScheduler:
    """Programador de alertas automáticas"""

    def __init__(self):
        self.system = CryptoAlertSystem()
        self.running = True

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Maneja señales de interrupción"""
        print("\n\n🛑 Deteniendo el programador...")
        self.running = False
        sys.exit(0)

    def run_analysis_job(self):
        """Tarea programada que ejecuta el análisis"""
        print("\n" + "🔄" * 25)
        print(f"⏰ EJECUCIÓN PROGRAMADA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔄" * 25)

        try:
            self.system.run(send_telegram=True)
        except Exception as e:
            print(f"❌ Error en ejecución programada: {e}")

        print(f"\n⏱️ Próxima ejecución en 5 minutos...")

    def start(self):
        """Inicia el programador"""
        print("""
    ╔══════════════════════════════════════════════╗
    ║   🤖 SISTEMA DE ALERTAS AUTOMÁTICO v2.0    ║
    ║   Ejecución cada 5 minutos                  ║
    ╚══════════════════════════════════════════════╝
        """)

        schedule.every(5).minutes.do(self.run_analysis_job)

        print("🚀 Ejecutando primer análisis...")
        self.run_analysis_job()

        print("\n⏳ Esperando próxima ejecución...")
        print("   Presiona Ctrl+C para detener.\n")

        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error en el bucle principal: {e}")
                time.sleep(5)


def main():
    """Función principal del scheduler"""
    scheduler = AlertScheduler()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n\n👋 Programa detenido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
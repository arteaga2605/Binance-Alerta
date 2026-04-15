#!/usr/bin/env python3
"""
Script para evaluar alertas pendientes.
Se puede ejecutar periódicamente (cada hora) vía cron o Task Scheduler.
"""

import sys
from binance_client import BinanceClient
from performance_tracker import PerformanceTracker


def main():
    print("🔍 Evaluando alertas pendientes...")
    client = BinanceClient()
    tracker = PerformanceTracker()
    count = tracker.evaluate_pending_alerts(client)
    print(f"✅ {count} alertas evaluadas.")


if __name__ == "__main__":
    main()
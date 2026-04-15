#!/usr/bin/env python3
"""
Genera un reporte de rendimiento comparativo entre analistas y un gráfico de barras.
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para entornos sin GUI
from performance_tracker import PerformanceTracker
import config


def generate_report():
    tracker = PerformanceTracker()
    summary = tracker.get_performance_summary()

    if not summary:
        print("No hay datos evaluados aún.")
        return

    print("\n" + "="*60)
    print("📊 REPORTE DE RENDIMIENTO DE ANALISTAS")
    print("="*60)

    analysts = []
    accuracies = []
    totals = []
    corrects = []
    avg_profits = []

    for analyst, data in summary.items():
        print(f"\n🔹 Analista: {analyst}")
        print(f"   Total señales: {data['total']}")
        print(f"   Aciertos: {data['correct']}")
        print(f"   Fallos: {data['incorrect']}")
        print(f"   Precisión: {data['accuracy']:.2f}%")
        print(f"   Profit promedio: {data['avg_profit']:.2f}%")
        print(f"   Profit total acumulado: {data['total_profit']:.2f}%")

        analysts.append(analyst)
        accuracies.append(data['accuracy'])
        totals.append(data['total'])
        corrects.append(data['correct'])
        avg_profits.append(data['avg_profit'])

    # Generar gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(analysts, accuracies, color=['#3498db', '#e74c3c'])
    ax.set_ylabel('Precisión (%)')
    ax.set_title('Comparativa de Precisión entre Analistas')
    ax.set_ylim(0, 100)

    # Añadir etiquetas con el valor
    for bar, acc, total, correct in zip(bars, accuracies, totals, corrects):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{acc:.1f}%\n({correct}/{total})',
                ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(config.REPORT_IMAGE_FILE, dpi=150)
    print(f"\n📈 Gráfico guardado en: {config.REPORT_IMAGE_FILE}")

    # También generar tabla detallada en CSV
    import csv
    csv_file = config.DATABASE_FILE.replace('.db', '_report.csv')
    all_alerts = tracker.get_all_evaluated_alerts()
    if all_alerts:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_alerts[0].keys())
            writer.writeheader()
            writer.writerows(all_alerts)
        print(f"📄 Detalle exportado a: {csv_file}")


if __name__ == "__main__":
    generate_report()
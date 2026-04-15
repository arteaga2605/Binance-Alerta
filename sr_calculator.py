"""
Cálculo de niveles de soporte y resistencia
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.signal import argrelextrema
from sklearn.cluster import KMeans
import warnings
import config


class SupportResistanceCalculator:
    """Calculador de niveles de soporte y resistencia"""

    def __init__(self, order: int = 5):
        """
        Args:
            order: Número de puntos para identificar extremos locales
        """
        self.order = order

    def find_local_extrema(self, df: pd.DataFrame, column: str = 'close',
                           extrema_type: str = 'both') -> Dict[str, List[float]]:
        """
        Encuentra máximos y mínimos locales en una serie de precios
        """
        if df.empty or len(df) < self.order * 2:
            return {'max': [], 'min': []}

        series = df[column].values

        # Encontrar máximos locales
        if extrema_type in ['max', 'both']:
            max_idx = argrelextrema(series, np.greater, order=self.order)[0]
            max_values = series[max_idx].tolist()
        else:
            max_values = []

        # Encontrar mínimos locales
        if extrema_type in ['min', 'both']:
            min_idx = argrelextrema(series, np.less, order=self.order)[0]
            min_values = series[min_idx].tolist()
        else:
            min_values = []

        return {'max': max_values, 'min': min_values}

    def cluster_levels(self, levels: List[float], n_clusters: int = 3,
                       eps: float = 0.02) -> List[float]:
        """
        Agrupa niveles similares usando K-Means para encontrar zonas clave
        """
        if not levels or len(levels) < 2:
            return levels

        # Limpiar niveles: eliminar duplicados y ordenar
        levels = sorted(list(set([l for l in levels if l > 0])))

        # Si hay menos niveles únicos que clusters deseados, devolver los niveles directamente
        if len(levels) <= n_clusters:
            return levels

        try:
            # Ajustar n_clusters para que no exceda el número de muestras únicas
            actual_clusters = min(n_clusters, len(levels))

            X = np.array(levels).reshape(-1, 1)

            # Suprimir warnings de convergencia de KMeans
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                kmeans = KMeans(n_clusters=actual_clusters,
                                random_state=42, n_init='auto')
                kmeans.fit(X)

            # Obtener centros de los clusters
            centers = sorted([c[0] for c in kmeans.cluster_centers_])

            # Fusionar clusters muy cercanos
            merged = []
            for center in centers:
                if not merged:
                    merged.append(center)
                elif abs(center - merged[-1]) / merged[-1] > eps:
                    merged.append(center)

            return merged

        except Exception as e:
            print(f"Error en clustering: {e}")
            return levels[:n_clusters]

    def calculate_pivot_levels(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula niveles de pivot point clásicos
        """
        if df.empty or len(df) < 1:
            return {}

        last_candle = df.iloc[-1]
        high = float(last_candle['high'])
        low = float(last_candle['low'])
        close = float(last_candle['close'])

        pivot = (high + low + close) / 3

        return {
            'pivot': pivot,
            'r1': 2 * pivot - low,
            'r2': pivot + (high - low),
            'r3': high + 2 * (pivot - low),
            's1': 2 * pivot - high,
            's2': pivot - (high - low),
            's3': low - 2 * (high - pivot)
        }

    def get_support_resistance_levels(self, df: pd.DataFrame,
                                      period_name: str) -> Dict[str, List[float]]:
        """
        Obtiene niveles de soporte y resistencia para un DataFrame
        """
        if df.empty:
            return {'support': [], 'resistance': []}

        # Encontrar extremos locales
        extrema = self.find_local_extrema(df, 'high', 'max')
        resistance_levels = extrema['max']

        extrema = self.find_local_extrema(df, 'low', 'min')
        support_levels = extrema['min']

        # También usar precios de cierre para niveles adicionales
        all_highs = df['high'].values
        all_lows = df['low'].values

        # Percentiles para niveles adicionales
        if len(df) > 5:
            resistance_levels.extend([
                np.percentile(all_highs, 95),
                np.percentile(all_highs, 90),
                np.percentile(all_highs, 85)
            ])

            support_levels.extend([
                np.percentile(all_lows, 5),
                np.percentile(all_lows, 10),
                np.percentile(all_lows, 15)
            ])

        # Agrupar niveles similares
        support_clustered = self.cluster_levels(support_levels, n_clusters=4)
        resistance_clustered = self.cluster_levels(resistance_levels, n_clusters=4)

        # Añadir niveles de pivot point
        pivot_levels = self.calculate_pivot_levels(df)
        if pivot_levels:
            support_clustered.extend([pivot_levels.get('s1', 0), pivot_levels.get('s2', 0)])
            resistance_clustered.extend([pivot_levels.get('r1', 0), pivot_levels.get('r2', 0)])

        # Filtrar y ordenar
        current_price = df['close'].iloc[-1]

        support_clustered = sorted([s for s in support_clustered if s > 0 and s < current_price])
        resistance_clustered = sorted([r for r in resistance_clustered if r > 0 and r > current_price])

        return {
            'support': support_clustered,
            'resistance': resistance_clustered
        }

    def get_all_levels(self, symbol: str, weekly_df: pd.DataFrame,
                       monthly_df: pd.DataFrame) -> Dict:
        """
        Obtiene todos los niveles de soporte y resistencia para un símbolo
        """
        weekly_levels = self.get_support_resistance_levels(weekly_df, "1_week")
        monthly_levels = self.get_support_resistance_levels(monthly_df, "1_month")

        # Combinar niveles únicos
        all_supports = sorted(list(set(weekly_levels['support'] + monthly_levels['support'])))
        all_resistances = sorted(list(set(weekly_levels['resistance'] + monthly_levels['resistance'])))

        return {
            'symbol': symbol,
            'supports': all_supports,
            'resistances': all_resistances,
            'weekly': weekly_levels,
            'monthly': monthly_levels
        }
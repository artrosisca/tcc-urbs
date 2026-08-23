"""
Geofencing and map-matching adapter module.
Delegates to TrajectoryReconstructor for backward compatibility.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from src.etl.trajectory import TrajectoryReconstructor, haversine_vectorized


def map_gps_to_shape(gps_lats: np.ndarray, gps_lons: np.ndarray, shape_lats: np.ndarray, shape_lons: np.ndarray) -> np.ndarray:
    """Backward-compatible wrapper for geometric shape projection."""
    return TrajectoryReconstructor.map_gps_to_shape(gps_lats, gps_lons, shape_lats, shape_lons)


def map_gps_to_shape_hmm(
    gps_lats: np.ndarray,
    gps_lons: np.ndarray,
    shape_lats: np.ndarray,
    shape_lons: np.ndarray,
    search_radius: float = 150.0,
    sigma_z: float = 30.0,
    beta: float = 50.0
) -> np.ndarray:
    """Backward-compatible wrapper for HMM Viterbi map-matching."""
    return TrajectoryReconstructor.map_gps_to_shape_hmm(
        gps_lats, gps_lons, shape_lats, shape_lons,
        search_radius=search_radius, sigma_z=sigma_z, beta=beta
    )


def resolve_sentido_and_shp(trip_df: pd.DataFrame, static_data: Dict[str, pd.DataFrame]) -> Tuple[Optional[str], Optional[Any]]:
    """Backward-compatible wrapper for static direction and shape ID resolution."""
    sentido_static, stops_filtered, shape_filtered = TrajectoryReconstructor.resolve_route_geometry(
        static_data,
        direction=trip_df['SENT'].iloc[0] if 'SENT' in trip_df.columns else "VOLTA",
        trip_sample_df=trip_df
    )
    shp_id = shape_filtered['SHP'].iloc[0] if (not shape_filtered.empty and 'SHP' in shape_filtered.columns) else None
    return sentido_static, shp_id


def match_trip_events(
    trip_df: pd.DataFrame,
    static_data: Dict[str, pd.DataFrame],
    line_code: Optional[str] = None,
    geofence_radius: float = 100.0,
    enforce_monotonicity: bool = True
) -> pd.DataFrame:
    """Backward-compatible wrapper for individual trip event matching."""
    return TrajectoryReconstructor.match_trip(
        trip_df,
        static_data,
        line_code=line_code,
        enforce_monotonicity=enforce_monotonicity
    )

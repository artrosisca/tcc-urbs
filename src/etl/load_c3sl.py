"""
Static data loading adapter module.
Delegates to TelemetryRepository for backward compatibility.
"""

import os
from src.etl.repository import default_telemetry_repo, FilesystemTelemetryAdapter, _parse_coord, _fix_encoding


def parse_coord(val):
    """Backward-compatible coordinate parser."""
    return _parse_coord(val)


def fix_encoding(text):
    """Backward-compatible encoding fixer."""
    return _fix_encoding(text)


def load_static_data(date_str, line_code, c3sl_dir="data/dados_c3sl"):
    """
    Backward-compatible wrapper to load static stops, timetable, and shape.
    """
    if c3sl_dir == "data/dados_c3sl":
        return default_telemetry_repo.get_static_data(date_str, line_code)
    # If custom c3sl_dir provided
    adapter = FilesystemTelemetryAdapter(base_data_dir=os.path.dirname(c3sl_dir) or "data")
    adapter.c3sl_dir = c3sl_dir
    return adapter.get_static_data(date_str, line_code)


if __name__ == "__main__":
    res = load_static_data("2025-10-24", "541")
    print("Pontos carregados:", len(res['pontos']))
    print("Tabela carregada:", len(res['tabela']))
    print("Shape carregado:", len(res['shape']))

# Pacote de Implementação — F1.7: Filtro de Outliers por Distância ao Shape (Traçado)

> **Para o executor:** implemente com TDD (teste primeiro → vermelho → implementação → verde) e rode a suíte completa de testes ao final. Meta: **89 testes passando** (88 atuais + 1 novo).

---

## 1. Contexto Metodológico (leia antes de codar)

- **Repo:** `/home/arosisca/GIT/tcc-urbs` · **Python:** `.venv/bin/python` · **Testes:** `.venv/bin/pytest tests/ -q`
- **Estado atual:** **88 testes passando** (61 dashboard E2E + 10 engine + 3 repository + 14 trajectory).
- **Problema metodológico identificado:**
  Hoje o método `clean_telemetry` em `src/etl/trajectory.py` (linhas ~73-88) filtra coordenadas GPS espúrias calculando a distância mínima a qualquer **parada planejada** (`outlier_threshold = 500.0m`).
  - **Problema 1:** Em linhas troncais ou interbairros (como a 541), existem trechos expressos onde a distância entre paradas consecutivas excede 1 km. Pings de telemetria emitidos no meio desse trecho (mesmo perfeitamente alinhados à via do ônibus) ficam a mais de 500m das duas paradas adjacentes e são descartados erroneamente como outliers.
  - **Problema 2:** Desvios operacionais reais ou trajetos curvos são censurados arbitrariamente por falta de proximidade a um poste físico de embarque.
- **Solução Correta:**
  A referência geométrica de um trajeto veicular é o **traçado da rota (shapeLinha)**, e não os pontos isolados de parada. Pings que estejam até 500m do traçado da linha são válidos; pings a mais de 500m do traçado são genuinamente anômalos.

---

## 2. Objetivo da Tarefa (F1.7)

1. Estender `clean_telemetry` em `src/etl/trajectory.py` com o parâmetro opcional `static_shape_df: Optional[pd.DataFrame] = None` e `shape_outlier_threshold: float = 500.0`.
2. Se `static_shape_df` for fornecido e não estiver vazio, o filtro de outliers calcula a distância mínima de cada ping aos vértices do **shape**, descartando pontos com distância > `shape_outlier_threshold`.
3. Se `static_shape_df` for nulo ou vazio, o método preserva o comportamento legado (distância a `static_stops_df`), garantindo **100% de retrocompatibilidade** com testes unitários existentes.
4. Em `reconstruct_event_log`, passar `static_shape_df=static_data.get('shape')` ao chamar `clean_telemetry`.
5. Adicionar teste unitário no padrão TDD demonstrando que pings entre paradas esparsas (>1km) são mantidos quando próximos ao shape, enquanto pings distantes do shape continuam descartados.

---

## 3. Restrições e Cuidados (não fazer)

- **NÃO quebrar testes existentes:** O teste `test_segmentation_fallback_progress_reversal` e outros testes que chamam `clean_telemetry` sem passar shape devem continuar passando perfeitamente.
- **NÃO alterar a ordem dos parâmetros posicionais** já existentes em `clean_telemetry(df_realtime, static_stops_df, distance_threshold, outlier_threshold, ...)`. Novos parâmetros devem ser opcionais com valor padrão no final da assinatura.
- **NÃO alterar** os dados processados históricos existentes em `data/dados_processados/`.

---

## 4. Implementação Passo a Passo

### Passo 1 — Teste primeiro (RED)

Criar o teste `test_clean_telemetry_filters_by_shape_distance` no final de `tests/test_trajectory_reconstruction.py`:

```python
def test_clean_telemetry_filters_by_shape_distance():
    """
    TDD Spec (F1.7):
    When static_shape_df is provided:
    1. A GPS ping situated 700m away from any stop, but directly on the route shape (~0m),
       MUST BE PRESERVED (not falsely discarded as an outlier).
    2. A GPS ping situated 2km away from the shape MUST BE DISCARDED as an outlier.
    """
    from datetime import datetime, timedelta

    # 2 paradas separadas por ~2km ao longo do eixo Norte-Sul (LAT ~ 0.018 graus ~ 2km)
    stops_df = pd.DataFrame([
        {"SEQ": 1, "NUM": "101", "NOME": "Parada Sul", "SENTIDO": "VOLTA", "LAT": -25.5350, "LON": -49.2710},
        {"SEQ": 2, "NUM": "102", "NOME": "Parada Norte", "SENTIDO": "VOLTA", "LAT": -25.5170, "LON": -49.2710},
    ])

    # Shape contínuo ligando as paradas
    shape_df = pd.DataFrame([
        {"SHP": "SHP_1", "LAT": -25.5350, "LON": -49.2710},
        {"SHP": "SHP_1", "LAT": -25.5260, "LON": -49.2710},  # meio do trecho (~1km de cada parada)
        {"SHP": "SHP_1", "LAT": -25.5170, "LON": -49.2710},
    ])

    base_time = datetime(2025, 10, 24, 8, 0, 0)
    raw_telemetry = pd.DataFrame([
        # Ping 1: Próximo à Parada Sul
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.5348, "LON": -49.2710, "request_timestamp": (base_time + timedelta(minutes=0)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
        # Ping 2: No meio do trecho expresso (LAT: -25.5260). Fica a ~1000m de ambas as paradas (> 500m), mas a 0m do shape!
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.5260, "LON": -49.2710, "request_timestamp": (base_time + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
        # Ping 3: Outlier legítimo (a 2km a leste do shape: LON: -49.2500)
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.5260, "LON": -49.2500, "request_timestamp": (base_time + timedelta(minutes=4)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
    ])

    # Com o filtro legado (apenas stops): o Ping 2 é descartado porque está a >500m de qualquer parada
    legacy_cleaned = TrajectoryReconstructor.clean_telemetry(raw_telemetry, static_stops_df=stops_df)
    assert len(legacy_cleaned) == 1  # Apenas Ping 1 sobreviveu

    # Com F1.7 (shape fornecido): o Ping 2 DEVE SOBREVIVER, e o Ping 3 DEVE SER DESCARTADO
    shape_cleaned = TrajectoryReconstructor.clean_telemetry(
        raw_telemetry,
        static_stops_df=stops_df,
        static_shape_df=shape_df
    )
    assert len(shape_cleaned) == 2
    # Confirma que os pings retidos foram exatamente o Ping 1 e o Ping 2 (meio do trecho)
    lats = shape_cleaned["LAT"].tolist()
    assert -25.5348 in lats
    assert -25.5260 in lats
```

Rodar:
`.venv/bin/pytest tests/test_trajectory_reconstruction.py::test_clean_telemetry_filters_by_shape_distance -q`
Deve falhar com `TypeError: TrajectoryReconstructor.clean_telemetry() got an unexpected keyword argument 'static_shape_df'` (RED).

---

### Passo 2 — Implementar (GREEN)

Em `src/etl/trajectory.py`:

1. Atualizar a assinatura de `clean_telemetry`:
```python
    @staticmethod
    def clean_telemetry(
        df_realtime: pd.DataFrame,
        static_stops_df: Optional[pd.DataFrame] = None,
        distance_threshold: float = 5.0,
        outlier_threshold: float = 500.0,
        static_shape_df: Optional[pd.DataFrame] = None,
        shape_outlier_threshold: float = 500.0
    ) -> pd.DataFrame:
```

2. Na etapa de filtro de outliers (substituindo ou condicionando o bloco das linhas ~73-88):
```python
        # 5. Outlier distance check: prefer route shape (trajectory path); fall back to stops if shape not provided
        ref_df = static_shape_df if (static_shape_df is not None and not static_shape_df.empty and 'LAT' in static_shape_df.columns) else static_stops_df
        threshold = shape_outlier_threshold if (static_shape_df is not None and not static_shape_df.empty and 'LAT' in static_shape_df.columns) else outlier_threshold

        if ref_df is not None and not ref_df.empty and 'LAT' in ref_df.columns:
            ref_lats = ref_df['LAT'].dropna().values
            ref_lons = ref_df['LON'].dropna().values
            if len(ref_lats) > 0:
                valid_gps = []
                for _, row in df.iterrows():
                    dists = haversine_vectorized(
                        np.full_like(ref_lats, row['LAT']),
                        np.full_like(ref_lons, row['LON']),
                        ref_lats,
                        ref_lons
                    )
                    valid_gps.append(bool(dists.min() <= threshold))
                df = df[valid_gps].copy()
```

3. Em `reconstruct_event_log`, passar `static_shape_df`:
```python
        df_clean = cls.clean_telemetry(
            realtime_df,
            static_data.get('pontos'),
            static_shape_df=static_data.get('shape')
        )
```

---

### Passo 3 — Verificar

1. `.venv/bin/pytest tests/test_trajectory_reconstruction.py::test_clean_telemetry_filters_by_shape_distance -q` → 1 verde.
2. `.venv/bin/pytest tests/test_trajectory_reconstruction.py -q` → 15/15 verdes.
3. `.venv/bin/pytest tests/ -q` → **89 passed** (suíte inteira).
4. `.venv/bin/pytest tests/test_dashboard_e2e.py -q` → 61 verdes intactos.

---

## 5. Critérios de Aceite

- [ ] Novo teste passa e antes falhava (TDD verificado).
- [ ] Pings em trechos com paradas >1km não são mais censurados quando sobre o shape.
- [ ] Pings espúrios distantes da rota continuam sendo descartados.
- [ ] Chamadas legadas sem `static_shape_df` mantêm comportamento original.
- [ ] Suíte completa: **89 passed**.

# Pacote de Implementação — F1.6: Taxa de Censura Operacional

> **Para o executor:** implemente com TDD (teste primeiro → vermelho → implementação → verde) e rode a suíte completa de testes ao final. Meta: **88 testes passando** (87 atuais + 1 novo).

---

## 1. Contexto Metodológico (leia antes de codar)

- **Repo:** `/home/arosisca/GIT/tcc-urbs` · **Python:** `.venv/bin/python` · **Testes:** `.venv/bin/pytest tests/ -q`
- **Estado atual:** **87 testes passando** (61 dashboard E2E + 10 engine + 3 repository + 13 trajectory).
- **Problema metodológico apontado pela banca:**
  Em `src/etl/trajectory.py`, o método `reconstruct_event_log` descarta viagens candidatas silenciosamente em dois momentos:
  1. Viagens com telemetria esparsa: `len(trip_group) < 3` pings.
  2. Viagens com alta interpolação sintética: `trip_events['interpolated'].mean() > 0.90` (>90% dos eventos estimados por PCHIP).
- **Necessidade para o TCC:**
  A banca examinadora exige transparência metodológica sobre a **Taxa de Censura Operacional** (*Censored Trip Rate*). O descarte de viagens não pode ser opaco; ele precisa ser quantificado, auditável e disponibilizado tanto via código quanto em arquivo sidecar JSON (`event_log_{line}_{tag}_stats.json`) ao salvar os dados processados.

---

## 2. Objetivo da Tarefa (F1.6)

1. Adicionar o parâmetro opcional retro-compatível `return_stats: bool = False` ao método `reconstruct_event_log`.
2. Coletar os seguintes contadores durante a reconstrução:
   - `total_candidate_trips`: total de grupos de viagens candidatas identificadas na segmentação.
   - `kept_trips`: total de viagens válidas retidas no log de eventos.
   - `dropped_insufficient_pings`: viagens descartadas por `len(trip_group) < 3`.
   - `dropped_high_interpolation`: viagens descartadas por `interpolated > 0.90`.
   - `censored_trip_rate`: razão de viagens descartadas em relação ao total: `(total_candidate_trips - kept_trips) / total_candidate_trips` (ou `0.0` se total for zero).
3. Gravar o sidecar JSON `event_log_{line_code}_{tag}_stats.json` no `output_dir` (quando informado).
4. Retornar `(df_log, stats)` quando `return_stats=True` e apenas `df_log` quando `return_stats=False` (mantendo 100% dos testes existentes verdes sem refatoração das chamadas antigas).

---

## 3. Restrições e Cuidados (não fazer)

- **NÃO quebrar retrocompatibilidade**: `return_stats` deve ter default `False`. Qualquer chamada existente que espera apenas um `pd.DataFrame` deve continuar recebendo apenas o DataFrame.
- **NÃO alterar** a lógica de segmentação nem os limites de corte (`< 3` pings e `> 0.90` interpolação continuam idênticos).
- **NÃO alterar** os arquivos de dados históricos em `data/dados_processados/`.
- **NÃO editar** nenhum teste existente em `tests/`.

---

## 4. Implementação Passo a Passo

### Passo 1 — Teste primeiro (RED)

Criar o teste `test_reconstruct_event_log_operational_censorship_stats` no final de `tests/test_trajectory_reconstruction.py`:

```python
def test_reconstruct_event_log_operational_censorship_stats(tmp_path, sample_static_data):
    """
    TDD Spec (F1.6):
    Operational censorship rate and counters must be recorded and reported:
    1. Trips with < 3 pings are dropped for insufficient pings.
    2. Trips with > 90% interpolated events are dropped for high interpolation.
    3. Valid trips are retained.
    When return_stats=True, returns (df_log, stats_dict).
    When output_dir is given, saves event_log_{line}_{tag}_stats.json.
    """
    import json
    from datetime import datetime, timedelta

    base_time = datetime(2025, 10, 24, 8, 0, 0)
    shape_pts = sample_static_data["shape"]

    # Cria 3 viagens distintas para o mesmo veículo:
    # Viagem 1 (trip_num=0): 2 pings apenas (deve cair em insufficient pings)
    v1 = [
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": shape_pts.iloc[0]["LAT"], "LON": shape_pts.iloc[0]["LON"], "ts": base_time, "SENT": "VOLTA", "TABELA": "1"},
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": shape_pts.iloc[1]["LAT"], "LON": shape_pts.iloc[1]["LON"], "ts": base_time + timedelta(seconds=20), "SENT": "VOLTA", "TABELA": "1"},
    ]

    # Viagem 2 (trip_num=1): 4 pings num ponto distante das paradas -> gerará >90% interpolação
    # (ou pings que mapeiam com alta interpolação)
    # Gap > 10 min força novo trip_num
    t2_base = base_time + timedelta(minutes=20)
    v2 = [
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.5000, "LON": -49.2500, "ts": t2_base + timedelta(seconds=i * 20), "SENT": "VOLTA", "TABELA": "1"}
        for i in range(4)
    ]

    # Viagem 3 (trip_num=2): 5 pings válidos ao longo do trajeto (deve ser mantida)
    t3_base = base_time + timedelta(minutes=50)
    v3 = [
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": shape_pts.iloc[i % len(shape_pts)]["LAT"], "LON": shape_pts.iloc[i % len(shape_pts)]["LON"], "ts": t3_base + timedelta(seconds=i * 20), "SENT": "VOLTA", "TABELA": "1"}
        for i in range(len(shape_pts))
    ]

    raw_df = pd.DataFrame(v1 + v2 + v3)

    df_log, stats = TrajectoryReconstructor.reconstruct_event_log(
        raw_df, sample_static_data, line_code="541",
        output_dir=str(tmp_path),
        return_stats=True
    )

    assert isinstance(stats, dict)
    assert "total_candidate_trips" in stats
    assert "kept_trips" in stats
    assert "dropped_insufficient_pings" in stats
    assert "dropped_high_interpolation" in stats
    assert "censored_trip_rate" in stats

    assert stats["total_candidate_trips"] == 3
    assert stats["dropped_insufficient_pings"] == 1
    assert stats["kept_trips"] == 1
    assert stats["censored_trip_rate"] == 2 / 3

    # Valida sidecar JSON
    stats_files = list(tmp_path.glob("event_log_541_*_stats.json"))
    assert len(stats_files) == 1
    with open(stats_files[0], 'r', encoding='utf-8') as f:
        saved_stats = json.load(f)
    assert saved_stats["total_candidate_trips"] == 3
    assert saved_stats["kept_trips"] == 1
```

Rodar:
`.venv/bin/pytest tests/test_trajectory_reconstruction.py::test_reconstruct_event_log_operational_censorship_stats -q`
Deve falhar com `ValueError: too many values to unpack (expected 2)` ou assinatura inválida (RED).

### Passo 2 — Implementar (GREEN)

Em `src/etl/trajectory.py`:

1. Adicionar `import json` no topo.
2. Atualizar a assinatura de `reconstruct_event_log`:
```python
    @classmethod
    def reconstruct_event_log(
        cls,
        realtime_df: pd.DataFrame,
        static_data: Dict[str, pd.DataFrame],
        line_code: str,
        output_dir: Optional[str] = None,
        date_range_tag: Optional[str] = None,
        return_stats: bool = False
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Dict[str, Any]]]:
```
3. Inicializar os contadores de estatística antes do loop de agrupamento:
```python
        stats = {
            "total_candidate_trips": 0,
            "kept_trips": 0,
            "dropped_insufficient_pings": 0,
            "dropped_high_interpolation": 0,
            "censored_trip_rate": 0.0
        }
```
4. No loop `for trip_num, trip_group in group.groupby('trip_num'):`:
   - Incrementar `stats["total_candidate_trips"] += 1`
   - Se `len(trip_group) < 3`: `stats["dropped_insufficient_pings"] += 1; continue`
   - Se `trip_events.empty`: continuar
   - Se `trip_events['interpolated'].mean() > 0.90`: `stats["dropped_high_interpolation"] += 1; continue`
   - Se mantida: `stats["kept_trips"] += 1`
5. Calcular `censored_trip_rate`:
```python
        total_cand = stats["total_candidate_trips"]
        kept = stats["kept_trips"]
        stats["censored_trip_rate"] = float((total_cand - kept) / total_cand) if total_cand > 0 else 0.0
```
6. Gravar sidecar JSON se `output_dir`:
```python
            stats_path = os.path.join(output_dir, f"event_log_{line_code}_{tag}_stats.json")
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
```
7. Ao final, retornar:
```python
        if return_stats:
            return df_log, stats
        return df_log
```
*(Tratar também os retornos antecipados quando `realtime_df` ou `static_data` forem vazios: se `return_stats`, retornar `(pd.DataFrame(), stats)`).*

### Passo 3 — Verificar

1. `.venv/bin/pytest tests/test_trajectory_reconstruction.py::test_reconstruct_event_log_operational_censorship_stats -q` → 1 verde.
2. `.venv/bin/pytest tests/test_trajectory_reconstruction.py -q` → 14/14 verdes.
3. `.venv/bin/pytest tests/ -q` → **88 passed** (suíte inteira).
4. `.venv/bin/pytest tests/test_dashboard_e2e.py -q` → 61 verdes intactos.

---

## 5. Critérios de Aceite

- [ ] Teste `test_reconstruct_event_log_operational_censorship_stats` passa e antes falhava (TDD verificado).
- [ ] Chamadas sem `return_stats` continuam retornando apenas `pd.DataFrame`.
- [ ] Suíte completa: **88 passed** (87 anteriores + 1 novo).
- [ ] Arquivo sidecar JSON gerado com os contadores corretos.
- [ ] Nenhum teste anterior foi modificado.

# Pacote de Implementação — F1.5: Corrigir mojibake na escrita do CSV de eventos

> **Para o executor (IA):** implemente **apenas** esta tarefa, com TDD, e rode a suíte inteira ao final. Não avance para outras tarefas. As próximas etapas serão entregues em pacotes separados.

---

## 1. Contexto (leia antes de codar)

- **Repo:** `/home/arosisca/GIT/tcc-urbs` · **Python:** `.venv/bin/python` · **Testes:** `.venv/bin/pytest tests/ -q`
- **Estado atual:** **86 testes passando** (61 dashboard E2E + 10 engine + 3 repository + 12 trajectory).
- O pipeline grava logs de eventos em `data/dados_processados/event_log_{linha}_{datas}.csv`. Arquivos **históricos** contêm nomes double-encoded (`SÃ£o`, `SÃ­tio`, `SÃ­`) — mojibake de encoding UTF-8 lido como Latin-1.
- Já existe o reparo `_fix_encoding(text)` em `src/etl/repository.py` (linha ~35), aplicado hoje **somente na leitura** de dados estáticos.
- Em `src/etl/trajectory.py`, o método `reconstruct_event_log` grava o CSV no bloco `if output_dir:` (final do método).

## 2. Objetivo da tarefa (F1.5)

Garantir que **todo CSV novo** seja gravado sem mojibake: aplicar `_fix_encoding` nas colunas textuais **antes** de `df_log.to_csv(...)`.

> ⚠️ **Não regenere/apague** os CSVs existentes em `data/dados_processados/` (o dado bruto do Regime B não existe no repositório). A leitura tolerante já existente deve continuar funcionando.

## 3. Restrições (não fazer)

- **Não** alterar o comportamento de omissão de paradas >150m em `match_trip`.
- **Não** reintroduzir `np.maximum.accumulate` em nenhum lugar.
- **Não** mexer em `activity_name_for_stop` / `strip_activity_name` (`src/etl/repository.py`).
- **Não** alterar `evaluate_conformance` (`src/mining/engine.py`).
- **Não** modificar testes existentes (apenas **adicionar** um novo).
- Ao usar a ferramenta de edição, o texto de busca (`oldString`) deve ser **idêntico** ao conteúdo do arquivo — leia o trecho antes.

## 4. Implementação passo a passo

### Passo 1 — Teste primeiro (RED)

Adicionar ao final de `tests/test_trajectory_reconstruction.py` (o arquivo já importa `os, pytest, pandas, numpy, datetime, timedelta` e `TrajectoryReconstructor`):

```python
def test_reconstruct_event_log_writes_clean_utf8(tmp_path, sample_raw_telemetry):
    """
    TDD Spec (F1.5):
    Even when static stop names arrive double-encoded (mojibake), the CSV written
    by reconstruct_event_log must contain clean UTF-8 names (no 'Ã' artifacts).
    """
    stops_df = pd.DataFrame([
        {"SEQ": 1, "NUM": "101", "NOME": "Terminal SÃ­tio Cercado", "SENTIDO": "VOLTA", "LAT": -25.5350, "LON": -49.2710},
        {"SEQ": 2, "NUM": "102", "NOME": "PraÃ§a do JapÃ£o", "SENTIDO": "VOLTA", "LAT": -25.4420, "LON": -49.2880},
        {"SEQ": 3, "NUM": "103", "NOME": "PraÃ§a Rui Barbosa", "SENTIDO": "VOLTA", "LAT": -25.4350, "LON": -49.2730},
    ])
    shape_df = pd.DataFrame([
        {"SHP": "SHP_1", "LAT": -25.5350, "LON": -49.2710},
        {"SHP": "SHP_1", "LAT": -25.4900, "LON": -49.2800},
        {"SHP": "SHP_1", "LAT": -25.4420, "LON": -49.2880},
        {"SHP": "SHP_1", "LAT": -25.4380, "LON": -49.2800},
        {"SHP": "SHP_1", "LAT": -25.4350, "LON": -49.2730},
    ])
    static_data = {"pontos": stops_df, "shape": shape_df, "tabela": pd.DataFrame()}

    df_log = TrajectoryReconstructor.reconstruct_event_log(
        sample_raw_telemetry, static_data, line_code="541",
        output_dir=str(tmp_path)
    )
    assert not df_log.empty

    csv_files = list(tmp_path.glob("event_log_541_*.csv"))
    assert csv_files, "CSV was not written"
    df_written = pd.read_csv(csv_files[0])
    assert not df_written['concept:name'].str.contains('Ã').any()
```

Rodar `.venv/bin/pytest tests/test_trajectory_reconstruction.py::test_reconstruct_event_log_writes_clean_utf8 -q` → deve **falhar** (RED).

### Passo 2 — Implementar (GREEN)

Em `src/etl/trajectory.py`:

1. Ampliar o import existente (linha ~14):

```python
from src.etl.repository import activity_name_for_stop, strip_activity_name, _fix_encoding
```

2. No bloco de gravação de `reconstruct_event_log`, **antes** de `df_log.to_csv(csv_path, index=False, encoding='utf-8')`, inserir:

```python
            # F1.5: ensure clean UTF-8 names on write (repair double-encoded mojibake)
            for col in ['concept:name']:
                if col in df_log.columns:
                    df_log[col] = df_log[col].apply(_fix_encoding)
```

> Nota: como `concept:name` é chave canônica (`PASSAGEM_{SEQ}_{NOME}`), reparar essa coluna basta para o log exportado. O XES é gravado a partir do mesmo `df_log`, portanto já sai limpo.

### Passo 3 — Verificar

1. `.venv/bin/pytest tests/test_trajectory_reconstruction.py -q` → 13/13 verdes (12 + 1 novo).
2. `.venv/bin/pytest tests/ -q` → **87 passed** (suíte inteira).
3. `.venv/bin/pytest tests/test_dashboard_e2e.py -q` → 61 verdes.

## 5. Critérios de aceite

- [ ] Novo teste passa e antes falhava (TDD respeitado).
- [ ] Suíte total: **87 passed** (era 86 + 1 novo).
- [ ] Nenhum arquivo em `data/dados_processados/` foi modificado ou apagado.
- [ ] Nenhum teste existente foi editado.

## 6. Reportar de volta (para o revisor)

1. Saída final do pytest (linha `N passed`).
2. `git diff --stat` dos arquivos alterados (esperado: 2 arquivos: `src/etl/trajectory.py` e `tests/test_trajectory_reconstruction.py`).
3. Qualquer desvio deste pacote, com justificativa.

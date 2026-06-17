# E2E Test Infra: URBS Process Mining Dashboard

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation internals.
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source | Tier 1 | Tier 2 | Tier 3 |
|---|---------|--------|:------:|:------:|:------:|
| 1 | Tab Navigation & Headers Emoji-Free | R1 | 5 | 5 | ✓ |
| 2 | Dynamic Bus Line Filtering | R2 | 5 | 5 | ✓ |
| 3 | Light Clean Visual Theme | R3 | 5 | 5 | ✓ |
| 4 | CartoDB Positron Map Tiles | R3 | 5 | 5 | ✓ |
| 5 | Repository Folder Reorganization | R4 | 5 | 5 | ✓ |

## Test Architecture
- **Test Runner**: A pytest-based suite located in `tests/test_dashboard_e2e.py`.
- **Test Invocation**: `pytest tests/test_dashboard_e2e.py -v` (using virtualenv python).
- **Directory Layout**:
  - `tests/` — Test files
  - `tests/test_dashboard_e2e.py` — Main E2E test file verifying all tiers

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Select Regime A, verify only Regime A processed bus lines are populated, map tiles are light theme, no emojis in headers | F1, F2, F3, F4 | Medium |
| 2 | Select Regime B, verify only Regime B processed bus lines are populated, check trips for line 541, verify API response | F1, F2, F5 | Medium |
| 3 | Run server under restructured directories, query all unique lines (empty regime) and ensure they are read from `data/` | F2, F5 | Medium |
| 4 | Select invalid regime/dates and check fallback to raw GPS line code listing from `data/dados_em_tempo_real_2026` | F2, F5 | High |
| 5 | Verify styles.css contains light background, dark/neutral active buttons, and app.js uses correct tile layer URL | F3, F4 | Low |

## Coverage Thresholds
- Tier 1: Feature Coverage (5 tests per feature = 25 cases)
- Tier 2: Boundary & Corner Cases (5 tests per feature = 25 cases)
- Tier 3: Cross-Feature Combinations (5 pairwise cases)
- Tier 4: Real-World Scenarios (5 application cases)
- **Total Minimum**: 60 test cases

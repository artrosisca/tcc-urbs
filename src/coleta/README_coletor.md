# Coletor de Dados em Tempo Real da URBS

Este script em Python coleta dados de geolocalização dos ônibus de Curitiba, consultando a API pública da URBS em intervalos regulares.

## O que o script faz

* **Coleta Contínua:** A cada 2 minutos (120 segundos), o script faz uma requisição à API da URBS para buscar a posição atual de todos os veículos.
* **Armazenamento Organizado:** Os dados coletados são salvos em arquivos CSV.
* **Estrutura de Pastas:** Para facilitar a análise, o script organiza os arquivos da seguinte forma:
    * Cria uma pasta principal (`dados_em_tempo_real`).
    * Dentro dela, cria uma pasta para o dia atual (ex: `2025-10-22`).
    * Dentro da pasta do dia, salva um arquivo CSV para cada hora (ex: `2025-10-22_17-00.csv`).
* **Agregação por Hora:** Todas as coletas feitas dentro de uma hora (ex: às 17:02, 17:04, 17:06...) são **anexadas** no mesmo arquivo CSV (`..._17-00.csv`).
* **Timestamping:** O script adiciona uma coluna `request_timestamp` em cada coleta, registrando a hora exata daquela "foto" dos dados.

## Robustez

O script é projetado para rodar 24/7 sem interrupção. Ele possui tratamento de erros para:
* Falhas de conexão com a internet ou API fora do ar.
* Erros ao salvar arquivos (como disco cheio).
* Se um erro ocorrer, ele registra a falha, espera o intervalo de 2 minutos e tenta novamente, sem "morrer".

## Campanhas de Coleta Realizadas (Regimes do TCC)

O coletor foi utilizado para capturar dois conjuntos de dados distintos (Regimes Operacionais) para fins de comparação metodológica no TCC:

| Característica | 1ª Coleta (Regime A - Amostragem Padrão) | 2ª Coleta (Regime B - Alta Frequência) |
| :--- | :--- | :--- |
| **Intervalo Nominal** | ~120 segundos (2 minutos) | ~20 segundos |
| **Data/Hora de Início** | `24/10/2025 02:32:48` | `02/12/2025 00:03:05` *(transmissões da linha 542 iniciam em `01/12 23:59:57`)* |
| **Data/Hora de Término**| `29/10/2025 12:29:23` | `08/12/2025 23:27:09` |
| **Duração Contínua** | **5 dias, 9 horas, 56 min e 35s** (~129,94 horas) | **6 dias, 23 horas, 24 min e 03s** (~167,40 horas / ~7 dias) |
| **Arquivos CSV** | 127 arquivos horários (distribuídos de `2025-10-24` a `2025-10-29`) | Processados e consolidados em logs de eventos |
| **Volume de GPS Bruto**| **5.082.166 registros** (toda a frota URBS) | Consolidado nos logs de eventos |
| **Ciclos de Snapshot** | 3.024 capturas de frota | Amostragem de alta taxa |
| **Event Log (Ex. L. 541)** | 12.949 eventos de paradas / 921 viagens | 16.822 eventos de paradas / 1.200 viagens |

> **Nota sobre Armazenamento:**
> - Os dados brutos horários residem originalmente no repositório `/home/arosisca/GIT/Coleta/coletor-URBS/dados_em_tempo_real/`.
> - No projeto `tcc-urbs`, esses dados são mapeados via link simbólico em `data/dados_em_tempo_real_2026/`.
> - Um arquivo de amostragem de teste pontual também está salvo em `2025-12-25/2025-12-25_20-00.csv` (1.417 registros).

## Requisitos

* Python 3
* Bibliotecas: `requests` e `pandas`

```bash
pip install requests pandas
```

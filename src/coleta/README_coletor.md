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

## Requisitos

* Python 3
* Bibliotecas: `requests` e `pandas`

```bash
pip install requests pandas

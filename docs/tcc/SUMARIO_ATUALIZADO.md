# Sumário Geral Atualizado do TCC

Este documento apresenta a estrutura definitiva do **Sumário da Monografia de Conclusão de Curso**, devidamente atualizada para refletir com fidelidade e rigor acadêmico todo o pipeline de engenharia de dados, os métodos de Mineração de Processos e a plataforma de software desenvolvida no projeto `tcc-urbs`.

---

## 1. Estrutura Canônica do Sumário (Normas ABNT / UTFPR)

```text
1 INTRODUÇÃO .................................................................... 15
  1.1 CONTEXTUALIZAÇÃO E DESAFIOS DO TRANSPORTE COLETIVO URBANO .................. 16
  1.2 PROBLEMA DE PESQUISA: DISCREPÂNCIAS ENTRE O PLANEJADO E O EXECUTADO ........ 18
  1.3 OBJETIVOS ................................................................. 20
      1.3.1 Objetivo Geral ...................................................... 20
      1.3.2 Objetivos Específicos ............................................... 20
  1.4 JUSTIFICATIVA E RELEVÂNCIA APLICADA ....................................... 21
  1.5 ESTRUTURA DA MONOGRAFIA ................................................... 23

2 REFERENCIAL TEÓRICO E ESTADO DA ARTE .......................................... 25
  2.1 FUNDAMENTOS DE MINERAÇÃO DE PROCESSOS ..................................... 25
      2.1.1 Os Três Pilares: Descoberta, Conformidade e Desempenho .............. 26
      2.1.2 Algoritmos de Descoberta: Do Alpha Miner ao Inductive Miner ......... 28
      2.1.3 Ecossistema de Ferramentas: ProM e PM4Py ............................ 30
  2.2 FORMALISMOS MATEMÁTICOS APLICADOS AO PROCESSO ............................. 32
      2.2.1 Redes de Petri e Semântica de Execução .............................. 32
      2.2.2 Verificação de Conformidade via Token-Based Replay .................. 34
      2.2.3 Grafos Diretamente-Seguidos (Directly-Follows Graphs - DFG) ......... 36
  2.3 TELEMETRIA VEICULAR E LOCALIZAÇÃO AUTOMÁTICA DE VEÍCULOS (AVL) ............ 38
      2.3.1 Natureza e Incertezas dos Dados de GPS em Ambientes Urbanos ......... 38
      2.3.2 Interfaces de Dados Abertos e APIs Governamentais no Transporte ..... 40
  2.4 RECONSTRUÇÃO DE TRAJETÓRIAS E MAP MATCHING ................................ 42
      2.4.1 Modelos Ocultos de Markov (HMM) e o Algoritmo de Viterbi ............ 43
      2.4.2 Interpolação Espaçotemporal Monotônica (PCHIP vs. Splines Cúbicos) .. 45
  2.5 TRABALHOS RELACIONADOS E LACUNAS DA LITERATURA ............................ 47
  2.6 SÍNTESE DO CAPÍTULO ....................................................... 50

3 METODOLOGIA E ENGENHARIA DE DADOS ............................................. 52
  3.1 VISÃO GERAL DA ARQUITETURA DA SOLUÇÃO ..................................... 52
  3.2 TRAMITAÇÃO INSTITUCIONAL E PROTOCOLO DE ACESSO AOS DADOS DA URBS .......... 54
  3.3 PROTOCOLO DE COLETA CONTÍNUA E CARACTERIZAÇÃO DOS REGIMES OPERACIONAIS ..... 56
      3.3.1 Coletor Autônomo e Campanhas de Telemetria (Regimes A e B) .......... 57
      3.3.2 Ingestão de Dados Cadastrais e Traçados Físicos (C3SL / URBS) ....... 59
  3.4 PRÉ-PROCESSAMENTO E FILTRAGEM COM RESTRIÇÃO NA MALHA VIÁRIA (SHAPE) ....... 61
  3.5 RECONSTRUÇÃO DE TRAJETÓRIAS E GERAÇÃO DO LOG DE EVENTOS ................... 64
      3.5.1 Segmentação Semântica de Viagens (Cases) ............................ 64
      3.5.2 Projeção Espacial HMM/Viterbi sobre o Traçado Físico ................ 66
      3.5.3 Estimação Temporal Monotônica via PCHIP e Limiar de Geocerca (150m) . 68
      3.5.4 Padronização com Chaves Canônicas e Incerteza de Sensoriamento ...... 71
      3.5.5 Mecanismo de Qualidade e Taxa de Censura Operacional ................ 73
  3.6 ESTRUTURAÇÃO E EXPORTAÇÃO DO LOG DE EVENTOS (PADRÃO IEEE 1849 / OPENXES) .. 75
  3.7 ARQUITETURA DA PLATAFORMA INTEGRADA DE AUDITORIA OPERACIONAL .............. 78
      3.7.1 Backend REST Reativo e Processamento Assíncrono com SSE (FastAPI) ... 78
      3.7.2 Frontend Analítico e Replay Geoespacial 4D em Alta Resolução (Deck.gl) 81
  3.8 PROTOCOLO DE VALIDAÇÃO E SUÍTE DE TESTES AUTOMATIZADOS (89 TESTES) ........ 84

4 RESULTADOS E DISCUSSÃO ........................................................ 87
  4.1 CARACTERIZAÇÃO DOS DATASETS OPERACIONAIS DA URBS .......................... 87
  4.2 AVALIAÇÃO DO IMPACTO DA CADÊNCIA DE AMOSTRAGEM (REGIME A VS. REGIME B) .... 90
  4.3 DESCOBERTA DE PROCESSOS: MODELOS REAIS E TRANSIÇÕES SILENCIOSAS (TAU) ..... 93
  4.4 VERIFICAÇÃO DE CONFORMIDADE: QUANTIFICAÇÃO DE DESVIOS E PARADAS OMITIDAS .. 97
  4.5 ANÁLISE DE DESEMPENHO: MAPEAMENTO DE GARGALOS OPERACIONAIS NO DFG ......... 102
  4.6 PLATAFORMA DE AUDITORIA OPERACIONAL NO CCO E REPLAY GEOESPACIAL ........... 107
  4.7 DISCUSSÃO DOS RESULTADOS E IMPACTOS NA FISCALIZAÇÃO DO TRANSPORTE ......... 112

5 CONSIDERAÇÕES FINAIS E CONCLUSÕES ............................................. 116
  5.1 SÍNTESE DAS CONTRIBUIÇÕES CIENTÍFICAS E METODOLÓGICAS ..................... 116
  5.2 CONTRIBUIÇÕES PRÁTICAS PARA A GESTÃO DO TRANSPORTE PÚBLICO DE CURITIBA .... 118
  5.3 LIMITAÇÕES METODOLÓGICAS DO TRABALHO ...................................... 120
  5.4 RECOMENDAÇÕES E TRABALHOS FUTUROS ......................................... 122

REFERÊNCIAS ..................................................................... 125
ANEXO A — DICIONÁRIO DE DADOS OPERACIONAIS DA API DA URBS ...................... 132
ANEXO B — ESTATÍSTICAS DETALHADAS DA SUÍTE DE TESTES AUTOMATIZADOS .............. 135
```

---

## 2. Comparativo Detalhado: Sumário Legado vs. Novo Sumário

| Capítulo | Estrutura Legada (Desatualizada) | Nova Estrutura Proposta (Atual) | Racional da Atualização |
| :--- | :--- | :--- | :--- |
| **Cap. 1** | Introdução genérica sem foco no problema da URBS. | Contextualização sólida sobre a Rede Integrada de Transporte (RIT) de Curitiba e delimitação precisa da discrepância entre o planejado e o executado. | Alinha o trabalho com a realidade empírica do município. |
| **Cap. 2** | Seção 2.2 abordava apenas "Geofencing e Junção Espacial simples". | Incorpora os formalismos matemáticos de **Redes de Petri**, **Token Replay**, **DFG**, **Modelos Ocultos de Markov (HMM)** e **Interpolação PCHIP**. | Eleva o embasamento teórico ao estado da arte de Mineração de Processos e GIS. |
| **Cap. 3** | Seção 3.3 intitulada "Construção do Log de Eventos via Geofencing e Junção Espacial". Sem menção a trâmites, regimes ou à plataforma web. | **Metodologia e Engenharia de Dados:** Documenta a tramitação com a URBS, a coleta dos Regimes A e B, o filtro de *outliers* no shape, o HMM/Viterbi, o PCHIP (150m), as chaves canônicas, a Taxa de Censura, a arquitetura da plataforma web (FastAPI/React/Deck.gl) e a suíte de 89 testes. | **Mudança crítica:** O capítulo passa a ser o espelho exato do código implementado e testado. |
| **Cap. 4** | Resultados restritos e sem conexão clara com o comparativo de amostragem. | Apresenta a análise comparativa entre os Regimes A e B, o impacto das transições silenciosas ($\tau$), o ranking real de paradas puladas, os gargalos do DFG e a validação no console do CCO. | Traz os dados reais extraídos diretamente dos experimentos executados na plataforma. |
| **Cap. 5** | Conclusão telegráfica e incompleta. | **Considerações Finais:** Sintetiza contribuições metodológicas, aplicabilidade direta na gestão pública da URBS, limitações honestas de sensoriamento e trabalhos futuros. | Fornece fechamento acadêmico e institucional consistente para a banca examinadora. |

---

## 3. Mapeamento de Arquivos no Repositório

Os textos completos correspondentes às seções reestruturadas estão localizados nos seguintes arquivos:

- **Diagrama Geral e Pipeline:** [`docs/tcc/DIAGRAMA_METODOLOGICO_COMPLETO.md`](file:///home/arosisca/GIT/tcc-urbs/docs/tcc/DIAGRAMA_METODOLOGICO_COMPLETO.md)
- **Capítulo 3 (Metodologia e Engenharia de Dados):** [`docs/tcc/capitulo-3-metodologia.md`](file:///home/arosisca/GIT/tcc-urbs/docs/tcc/capitulo-3-metodologia.md)
- **Capítulo 4 (Resultados e Discussão):** [`docs/tcc/capitulo-4-resultados.md`](file:///home/arosisca/GIT/tcc-urbs/docs/tcc/capitulo-4-resultados.md)
- **Capítulo 5 (Considerações Finais e Conclusões):** [`docs/tcc/capitulo-5-conclusao.md`](file:///home/arosisca/GIT/tcc-urbs/docs/tcc/capitulo-5-conclusao.md)
- **Guia do Dashboard e Apresentação:** [`docs/reuniao_orientador/GUIA_COMPLETO_DO_PROJETO.md`](file:///home/arosisca/GIT/tcc-urbs/docs/reuniao_orientador/GUIA_COMPLETO_DO_PROJETO.md)
- **Suíte de Testes Automatizados (89 testes):** [`tests/`](file:///home/arosisca/GIT/tcc-urbs/tests/)

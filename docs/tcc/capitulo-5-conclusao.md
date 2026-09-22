# Capítulo 5 — Considerações Finais e Conclusões

Este capítulo sintetiza as conclusões alcançadas ao término da pesquisa, resgatando os objetivos formulados inicialmente, destacando as principais contribuições científicas e tecnológicas decorrentes da engenharia de dados implementada, explicitando as limitações metodológicas identificadas ao longo das campanhas experimentais e pontuando recomendações concretas para a evolução de políticas públicas e trabalhos futuros no setor de mobilidade urbana.

---

## 5.1 Conclusões e Síntese das Contribuições Metodológicas

O objetivo precípuo deste trabalho — transformar registros brutos, ruidosos e esparsos de telemetria veicular (GPS) da API pública da URBS em registros de eventos padronizados (*event logs*) para aplicação analítica por técnicas de Mineração de Processos — foi plenamente consolidado. A pesquisa comprovou que a operação de transporte público por ônibus é eminentemente orientada a processos de negócio, podendo ser modelada formalmente sob a semântica de casos (*trips*), atividades discretas de passagem e sequências temporais de execução.

Dentre as contribuições metodológicas originais alcançadas pela pesquisa, destacam-se:

1. **Superação do Geofencing Simplista por Reconstrução Topológica Rigorosa:** A introdução do algoritmo de *Map Matching* probabilístico baseado em Modelos Ocultos de Markov (HMM/Viterbi), associado à interpolação temporal PCHIP com garantia de monotonicidade ($dt/ds \ge 0$), superou com folga as falhas de causalidade e aceleração irreal observadas em métodos legados de splines cúbicos e junção espacial simples.
2. **Engenharia de Logs de Eventos com Qualidade Explícita e Chaves Canônicas:** A adoção de chaves unívocas de atividade no formato `PASSAGEM_{SEQ:02d}_{NOME}` erradicou as "pulas fantasma" e os laços repetitivos espúrios em paradas com denominações homônimas. Além disso, a segregação explícita entre incerteza amostral (`interpolated: bool`) e omissão deliberada (limiar de geocerca de 150m) permitiu auditar desvios de rota com honestidade matemática.
3. **Formalização da Taxa de Censura Operacional e Filtro Viário Baseado no Shape:** A validação espacial contra os segmentos contínuos da geometria viária oficial (`shapeLinha`), com tolerância de 500m, impediu o descarte indevido de registros em corredores expressos arteriais. O estabelecimento de uma taxa de censura automática impediu que viagens degradadas por apagões de hardware de GPS contaminassem os modelos indutivos de processo.
4. **Comprovação Empírica do Impacto da Cadência Amostral:** A análise comparativa entre o Regime A (~120s) e o Regime B (~20s) forneceu subsídios quantitativos inéditos sobre a sensibilidade dos algoritmos de *Process Mining* ao intervalo de coleta: enquanto a telemetria de 2 minutos resulta em quebra artificial de conformidade (*Trace Fitness* em torno de 0,38–0,46 decorrente da baixa resolução temporal), a cadência de 20 segundos viabiliza aderências operacionais excepcionais (95,2% a 100% de casos conformes), demonstrando a viabilidade técnica da mineração contínua em alta taxa.
5. **Implementação de Plataforma Full-Stack Funcional e Auditável:** O desenvolvimento de uma aplicação web integrada (FastAPI + React + Deck.gl v9), provida de streaming assíncrono (SSE) e 82 testes automatizados contínuos, demonstrou a exequibilidade de transpor a teoria de Mineração de Processos em uma ferramenta prática de fiscalização e governança para operadoras de transporte.

---

## 5.2 Contribuições Práticas para a Gestão do Transporte de Curitiba

Os resultados obtidos ultrapassam o escopo puramente acadêmico ao oferecerem aplicações práticas diretas para a gestão da Rede Integrada de Transporte (RIT) e a governança operacional da URBS:

- **Fiscalização Automatizada de Cumprimento de Itinerário:** O módulo executivo de *Auditoria Diária CCO* capacita os fiscais de transporte com uma ferramenta de triagem imediata, capaz de ranquear em segundos quais veículos e linhas violaram o dever de atendimento a paradas e terminais, substituindo conferências manuais e passivas baseadas em queixas de passageiros por auditoria ativa baseada em dados.
- **Detecção Cirúrgica de Gargalos Físicos (Gargalos do DFG):** A análise pelo Grafo Diretamente-Seguido (DFG) revelou com clareza matemática os nós viários responsáveis pelas maiores retenções operacionais da frota (como o trecho de saída do Terminal Sítio Cercado, cuja duração média observada atinge 7,12 minutos). Esse diagnóstico fornece insumo qualificado para a Secretaria Municipal de Trânsito priorizar obras de engenharia de tráfego, faixas exclusivas ou reprogramação semafórica inteligente.
- **Racionalização Contratual e Subsídios de Operação:** Métricas objetivas de conformidade topológica e pontualidade por tabela horária fornecem uma base de auditoria imparcial para a aferição de metas contratuais e remuneração quilométrica das empresas concessionárias que operam o sistema de ônibus da capital.

---

## 5.3 Limitações Metodológicas do Estudo

A despeito da robustez e consistência dos resultados obtidos, o presente trabalho circunscreve-se sob as seguintes limitações metodológicas:

1. **Ausência de Sensoriamento de Portas e Telemetria Fina (*Ground Truth* AVL):** O pipeline fundamenta-se estritamente na telemetria GPS transmitida via API pública, não dispondo de sensores de abertura/fechamento de portas ou catracas eletrônicas para mensurar o tempo físico real de embarque e desembarque. Assim, a passagem pelo ponto atesta presença espacial, mas não afere o tempo de embarque efetivo.
2. **Natureza Unidimensional do Map Matching:** A projeção de trajetórias é restrita e condicionada aos nós do traçado oficial cadastrado (`shapeLinha`). Caso o motorista execute um desvio severo por vias paralelas secundárias, o sistema aponta corretamente a omissão das paradas planejadas, mas o traçado geoespacial de replay não reconstrói o percurso alternativo fora da rota oficial, por não incorporar o grafo viário irrestrito de Curitiba (e.g., OpenStreetMap).
3. **Assimetria de Armazenamento entre Regimes:** Devido ao expressivo volume de dados gerado pela coleta contínua em alta taxa (mais de 40 milhões de leituras estimadas em 7 dias), o repositório local preserva os dados brutos de GPS apenas do Regime A, mantendo o Regime B representado por seus registros de eventos já consolidados e validados, limitando o reprocessamento de novas linhas apenas para a amostragem de outubro/2025.
4. **Dependência da Qualidade do Sinal GPS de Terceiros:** Flutuações de conectividade das operadoras de telefonia celular e imprecisões no receptor GPS dos veículos continuam demandando limiares empíricos de tolerância (como a geocerca de 150m e a restrição de 500m no shape), os quais podem requerer recalibração caso a tecnologia embarcada da frota venha a ser modernizada.

---

## 5.4 Recomendações e Trabalhos Futuros

Como desdobramentos naturais e oportunidades de expansão a partir da infraestrutura aqui construída, sugerem-se as seguintes linhas de investigação e desenvolvimento:

1. **Integração com Dados de Bilhetagem Eletrônica e Matriz Origem-Destino:** Cruzar o log de eventos de passagem com os registros de validação de cartões de transporte nas catracas dos ônibus, viabilizando a análise de conformidade centrada na jornada do usuário e na detecção de superlotação em tempo real.
2. **Expansão do Map Matching para Grafos Urbanos Completos:** Implementar algoritmos de *map matching* sobre a malha viária integral do OpenStreetMap (OSM) via bibliotecas como `osmnx` ou `Valhalla`, permitindo a reconstrução exata da rota física desviada quando o ônibus trafegar por vias clandestinas ou paralelas.
3. **Varredura Paramétrica Sistemática (*Parameter Sweep*):** Conduzir experimentos automatizados de sensibilidade variando os hiperparâmetros de Viterbi ($\sigma_z \in [10, 50]\text{ m}$ e $\beta \in [20, 100]\text{ m}$) e o raio de geocerca ($r \in [50, 250]\text{ m}$), quantificando a estabilidade dos gargalos do DFG frente às variações do estimador.
4. **Desenvolvimento de Módulos de Aprendizado de Máquina Preditivo:** Acoplar modelos de aprendizado profundo (*Long Short-Term Memory* — LSTM ou *Graph Neural Networks* — GNN) aos logs de eventos gerados, prevendo atrasos e propagação de engarrafamentos em cascata com 15 a 30 minutos de antecedência.
5. **Incorporação em Ambiente Produtivo no CCO da URBS:** Promover um projeto piloto de transferência tecnológica junto aos gestores de tráfego de Curitiba, validando a plataforma em escala operacional para monitoramento em tempo real de todas as linhas troncais e alimentadoras da capital.
# Sumário do TCC - Versão Final Alinhada com o Orientador

Este documento apresenta a versão ajustada do sumário, seguindo rigorosamente as recomendações do orientador (Prof. André Pinz Borges):

1. Linguagem natural e sem jargões artificiais: substituição de termos como "cadência de amostragem" por termos simples e objetivos como "intervalos de coleta".
2. Sem travessões: uso de pontuação padrão (vírgulas, parênteses e pontos), evitando construções típicas de geradores de texto.
3. Testes nos Resultados: a validação da plataforma e os testes automatizados ficam no Capítulo 4.
4. Dados na Metodologia: a descrição do dataset e dos regimes de coleta de dados da URBS fica no Capítulo 3.
5. Cenários bem definidos: a seção 4.1 inclui tabela comparativa e subseções claras para as linhas analisadas no trabalho (541, 542 e 010).

---

## Estrutura do Sumário

```text
1 INTRODUÇÃO
  1.1 OBJETIVOS
      1.1.1 Objetivo Geral
      1.1.2 Objetivos Específicos
  1.2 JUSTIFICATIVA
  1.3 ESTRUTURA DO TRABALHO

2 FUNDAMENTAÇÃO TEÓRICA E REVISÃO DA LITERATURA
  2.1 CONCEITOS DE MINERAÇÃO DE PROCESSOS
      2.1.1 Descoberta, Conformidade e Desempenho
      2.1.2 Algoritmos de Descoberta: Alpha Miner e Inductive Miner
      2.1.3 Ferramentas de Mineração de Processos: ProM e PM4Py
  2.2 ANÁLISE DE DADOS EM TRANSPORTE PÚBLICO
      2.2.1 Dados de GPS e Mobilidade Urbana
      2.2.2 APIs de Dados Abertos no Transporte Público
      2.2.3 Ajuste de Rotas (Map-Matching) e Interpolação de Trajetórias
  2.3 TRABALHOS RELACIONADOS
      2.3.1 Aplicações de Mineração de Processos no Transporte
      2.3.2 Análise Operacional de Frotas de Ônibus
      2.3.3 Comparativo dos Trabalhos Correlatos
  2.4 SÍNTESE DO CAPÍTULO

3 METODOLOGIA E ENGENHARIA DE DADOS
  3.1 Arquitetura Geral da Solução
  3.2 Coleta e Características dos Dados da URBS
  3.3 Regimes de Coleta de Dados (Regime A de 2m e Regime B de 20s)
  3.4 Filtragem dos Dados pelo Traçado da Linha (Shape)
  3.5 Reconstrução de Trajetórias e Geração de Viagens
      3.5.1 Separação e Identificação das Viagens (Trips)
      3.5.2 Ajuste dos Pontos de GPS ao Traçado da Linha (Map-Matching)
      3.5.3 Identificação das Paradas e Horários de Passagem
      3.5.4 Tratamento de Incertezas do GPS e Gaps de Coleta
      3.5.5 Critérios de Qualidade e Descarte de Viagens Incompletas
  3.6 Formatação do Log de Eventos no Padrão OpenXES
  3.7 Desenvolvimento da Plataforma Web e Dashboard de Monitoramento

4 RESULTADOS E DISCUSSÃO
  4.1 Caracterização dos Cenários Experimentais
      4.1.1 Cenário 1: Linha Troncal Radial (Linha 541 - Bairro Novo A)
      4.1.2 Cenário 2: Linha Alimentadora (Linha 542 - Bairro Novo B)
      4.1.3 Cenário 3: Linha Circular Interbairros (Linha 010 - Interbairros I)
  4.2 Comparação entre os Intervalos de Coleta (20s vs. 2 min)
  4.3 Modelos Operacionais Descobertos nas Linhas
  4.4 Avaliação de Conformidade e Detecção de Paradas Omitidas
  4.5 Identificação de Gargalos e Tempos de Percurso
  4.6 Validação do Dashboard e Testes Automatizados da Plataforma
  4.7 Aplicação dos Resultados na Fiscalização do Transporte

5 CONSIDERAÇÕES FINAIS
  5.1 Conclusões do Trabalho
  5.2 Contribuições para a Gestão do Transporte
  5.3 Dificuldades e Limitações Encontradas
  5.4 Propostas de Trabalhos Futuros

REFERÊNCIAS
```

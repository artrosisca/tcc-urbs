# Guia Completo do Projeto: Mineração de Processos no Transporte Público (URBS)
**Material de Apoio para Reunião de Orientação**

Este documento centraliza todas as informações essenciais sobre o estado atual do projeto, desde as melhorias de pipeline até a interpretação de cada tela do Dashboard. Ideal para guiar a apresentação e responder a dúvidas técnicas.

---

## 1. Resumo Executivo: O que foi resolvido?

O coração matemático do projeto (Pipeline ETL) foi completamente refatorado para garantir que o modelo represente a realidade com altíssimo rigor acadêmico:

* **Filtro Geométrico (Shape):** O GPS não é mais validado por círculos ingênuos em volta dos pontos (que falhavam em vias expressas longas). O ônibus agora é rastreado matematicamente por cima do traçado contínuo da via.
* **Chaves Canônicas:** Nomes de paradas repetidas ao longo de uma mesma linha (ex: duas paradas com o mesmo nome na mesma avenida) antes quebravam a mineração. Agora o sistema injeta a "sequência" no nome (ex: `PASSAGEM_01_ESTACAO`), tornando cada parada única.
* **Taxa de Censura Operacional:** Viagens com sinal de GPS intermitente ou corrompido são automaticamente expurgadas do sistema. O painel contabiliza exatamente qual foi a taxa de "lixo" removida.

---

## 2. Guia do Dashboard: Como ler as Telas?

A interface do painel divide o projeto entre a "Visão de Negócio" (CCO) e o "Rigor Algorítmico" (Process Mining). Todos os algoritmos visuais foram migrados para renderizadores nativos do framework **PM4Py**.

### Aba 1: Auditoria Diária (Visão CCO)
* **O que é:** O relatório executivo final. Uma tabela de ranqueamento que mostra imediatamente quais viagens/motoristas mais desviaram da rota e cometeram infrações (paradas puladas).
* **Como usar na apresentação:** Enfatize que clicar sobre qualquer ônibus problemático da tabela ativa automaticamente a lente investigativa (Drill-down), levando você para o Mapa onde o trajeto deste único infrator será reproduzido isoladamente.

### Aba 2: Mapa de Replay
* **O que é:** A visualização geoespacial (GIS). Usa tecnologia de alto desempenho (Deck.gl) para reproduzir a movimentação dos ônibus nas ruas.
* **Como ler:** Você verá pontos que deslizam ao longo do trajeto (linhas contínuas). Os balões brancos mostram o ID real do veículo. A barra de controle de tempo se autoajusta perfeitamente ao período em que as frotas estiveram rodando de fato.

### Aba 3: Descoberta (Rede de Petri)
* **O que é:** O fluxo processual teórico gerado nativamente pelo framework PM4Py (Process Mining).
* **Como interpretar o Grafo:**
  * **Retângulos (Transições):** Representam a chegada do ônibus a um Ponto de Parada específico.
  * **Círculos Verdes (Places):** São os estados do sistema (o trajeto físico entre duas paradas). O "Token" (ponto) viaja por dentro deles.
  * **Arestas (Setas):** Mostram a ordem estrita e lógica que o ônibus *deve* percorrer.
  * **Marcas Vermelhas (Gaps):** Quando o sistema aplica o log real sobre este modelo ideal e um ônibus fura a fila (pula uma parada), o modelo sinaliza transições com bordas vermelhas e tokens que faltaram. Essa é a "prova do crime".

### Aba 4: Conformidade
* **O que é:** Uma métrica puramente quantitativa. Representa em números percentuais o quão fiel (fitness) a frota foi em relação à Rede de Petri idealizada. Mostra quantas paradas no total foram puladas no período estudado.

### Aba 5: Desempenho (DFG - Directly-Follows Graph)
* **O que é:** O perfilador de gargalos operacionais da cidade, gerado nativamente pelo PM4Py.
* **Como interpretar o Grafo:**
  * Ao contrário da Rede de Petri, o DFG foca no **tempo médio** de trânsito.
  * **Nós (Bolinhas Pretas):** São as paradas de ônibus.
  * **Arestas (Setas):** Elas informam o Tempo de Viagem (ex: 2 min, 15 seg) registrado para ir do ponto A ao ponto B.
  * Você pode facilmente bater o olho no DFG e identificar engarrafamentos históricos, observando quais setas registram as maiores demoras absolutas (gargalos).

---

## 3. Pautas e Defesas Técnicas (Perguntas Frequentes)

Estas são as respostas prontas para defender decisões de arquitetura cruciais:

**Pergunta 1: Por que o "Map Matching" no Mapa de Replay não acompanha as ruas alternativas que o motorista fez para "cortar caminho", forçando o ônibus a andar sobre a rota oficial?**
> **Resposta:** "Porque este é um projeto estritamente focado em **Mineração de Processos** e não em Sistemas Globais de Roteamento (GIS). Nosso *Map Matching* é unidimensional: ele mapeia tudo contra a malha oficial. Se o motorista entra em uma rua paralela, o sistema deduz a omissão lógica da parada no evento (Token-Based Replay), mas a visualização é fisicamente ancorada na rota conhecida para evidenciar quebra de conformidade. Para seguir ruas aleatórias, seria necessário carregar o Grafo Completo de Ruas da Cidade (OpenStreetMap) no servidor. Fica catalogado como **Trabalhos Futuros**."

**Pergunta 2: E como o sistema crava que a parada foi pulada? Como funciona a distância?**
> **Resposta:** "Usamos uma arquitetura híbrida muito superior a um simples círculo de Geofencing. No backend, traçamos um gatilho paramétrico de Tolerância de **150 metros**. O algoritmo mede a distância (Fórmula de Haversine) entre todos os *pings* do GPS e o ponto oficial. Se a distância for superior a 150m em todo o percurso, a parada é cortada (infração registrada). Mas, se for menor que 150m, o algoritmo invoca um mecanismo matemático poderoso chamado **PCHIP Interpolator**, que ajusta a velocidade do ônibus com as coordenadas e descobre, até na fração de milissegundo, a exata marcação de tempo em que a porta do ônibus se alinhou à calçada oficial do ponto."


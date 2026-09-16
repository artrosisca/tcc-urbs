# Resumo do Status do Projeto (TCC URBS Process Mining)

Este documento resume de forma simples o que foi resolvido no código, no pipeline de dados e na tela do projeto recentemente.

## 1. Melhorias nos dados e na precisão (Pipeline)

Para garantir que o modelo de *Process Mining* represente a realidade dos ônibus, fizemos as seguintes correções:

*   **Filtro pela Rota (Shape) em vez de "Bolhas" (Geofence):** 
    Antes, o sistema descartava o GPS do ônibus se ele ficasse fora de um raio (geofence) ao redor de cada parada. O problema é que em vias expressas longas, o sistema achava que o ônibus era um erro e apagava o dado. Agora, a validação é feita contra o **desenho contínuo da rua** (Shape da rota), resolvendo esse problema e mantendo as viagens válidas.
*   **Paradas sem nome repetido (Chave Canônica):** 
    Como a URBS às vezes repete o nome de estações diferentes, o algoritmo achava que o ônibus estava "pulando" de uma ponta a outra da cidade. Agora nós juntamos o número da sequência com o nome (`PASSAGEM_01_ESTACAO`). Isso consertou quase 100% das falsas anomalias.
*   **Taxa de Censura (Saber o que é lixo):** 
    Criamos um contador que anota exatamente quantas viagens foram ignoradas porque o GPS estava muito ruim (ex: viagens com menos de 3 pontos de GPS salvos). Assim, limpamos o modelo sem esconder o que foi jogado fora.
*   **Aviso de Dados Adivinhados (Interpolação):**
    Quando o GPS falha e o algoritmo precisa deduzir o percurso (interpolação), esse dado agora ganha uma "etiqueta". Com isso, quando o dashboard calcula o tempo de viagem ou gargalos de trânsito, ele ignora esses dados inventados e usa apenas as marcações reais do GPS.

## 2. Melhorias na Tela (Dashboard)

A interface também foi melhorada para apresentar os resultados de forma mais clara:

*   **Porcentagem Real de Erros:** O painel de Conformidade agora calcula a porcentagem correta de vezes que uma parada foi pulada em relação ao total de viagens, usando cores (verde/amarelo/vermelho) para alertar problemas graves.
*   **Grafo Perfeito (Rede de Petri):** O mapa lógico do processo foi atualizado. Paramos de usar um layout de "bolhas soltas" e passamos a usar o gerador nativo do algoritmo (Graphviz). Agora o fluxo sai perfeito da esquerda para a direita, com suporte a zoom pelo mouse.
*   **Filtros Limpos:** A barra lateral de controles ficou mais limpa. Botões muito técnicos (como escolher qual Regime de coleta usar ou ler os logs de terminal) foram escondidos numa aba de "Configurações Avançadas".

## 3. Em que fase estamos?

1. **Texto (TCC):** A parte de Metodologia e Resultados já está sendo sincronizada com as mudanças acima.
2. **Código:** O coração do projeto (pipeline) já está finalizado, com 89 testes automáticos garantindo que nada quebre.
3. **Falta pouco na Interface:** Faltam só três detalhes rápidos (F2.6, F2.7 e F2.8), como arrumar o "slider" de tempo no mapa e fazer com que ao clicar em um ônibus na tabela de erros, o mapa foque direto nele.

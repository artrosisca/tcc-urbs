# Pautas Técnicas e Argumentações para Reunião com Orientador

Este documento reúne respostas e argumentos técnicos avançados para defender as escolhas de arquitetura do projeto durante reuniões de orientação ou perante a banca avaliadora.

## 1. Por que o Map Matching não exibe as ruas alternativas que o ônibus pegou no desvio?

Na teoria pura de Sistemas de Informação Geográfica (GIS), mapear um desvio real exige cruzar os pontos de GPS com o **Grafo Completo de Ruas da Cidade** (usando motores de roteamento avançados como OpenStreetMap, OSRM ou GraphHopper). 

**Nossa Abordagem (Map Matching 1D):**
O Map Matching construído neste TCC é domínio-específico para transporte público. Ele conhece exclusivamente a geometria da **rota oficial** (o arquivo de `shape` fornecido pela URBS). Quando um ônibus foge da rota, o nosso algoritmo não "descobre" qual rua lateral ele pegou; em vez disso, ele tenta projetar os pings de GPS perdidos para o ponto mais próximo da rota oficial conhecida.
Na prática, o ônibus é renderizado visualmente percorrendo o asfalto oficial a toda velocidade entre a parada anterior e a posterior à infração, omitindo o traçado físico do atalho.

**Argumento para a Banca (Trabalhos Futuros):**
*"A arquitetura atual foca estritamente na Conformidade de Processos (pulou ou não a parada). A descoberta do traçado físico das rotas de fuga exige roteamento em grafo de ruas de malha aberta (OpenStreetMap). Esta expansão foi catalogada como o principal Trabalho Futuro do projeto."*

## 2. Como funciona o gatilho de Parada? Ainda usamos Geofencing?

O projeto evoluiu do Geofencing tradicional (um simples círculo de raio fixo ao redor do ponto) para um mecanismo híbrido de **Tolerância Geométrica + Interpolação Matemática (PCHIP)**.

**Mecânica de Corte (Tolerância de 150 metros):**
1. O algoritmo mede a distância física (via fórmula de *Haversine*) entre o Ponto de Parada oficial e **todos** os pings de GPS registrados naquela viagem do ônibus.
2. A tolerância máxima (Geofence residual) configurada no código (`max_stop_distance`) é de **150 metros**. 
3. Se a distância mínima que o ônibus chegou daquele ponto for **maior que 150 metros**, o algoritmo declara que a parada foi sumariamente ignorada (skipped) e ela é cortada do Log de Eventos.

**Interpolação de Precisão:**
Se o ônibus chegou dentro desse raio de tolerância de 150m, o algoritmo aciona o interpolador `PchipInterpolator`. Essa função matemática avalia a velocidade, o traçado da via e o tempo dos pings adjacentes para calcular até a fração de segundo exata em que as portas do ônibus se alinharam perfeitamente ao poste de parada.

**Argumento para a Banca:**
*"Não usamos um Geofencing burro que registra a presença no momento que o ônibus 'toca' a borda do círculo. O raio de 150 metros atua estritamente como um filtro de corte de outliers (desvios graves). Para os eventos válidos, a marcação de tempo (timestamp) no Event Log é cravada matematicamente pela projeção da trajetória no centro exato da parada."*

document.addEventListener("DOMContentLoaded", () => {
    // ESTADO GLOBAL DO DASHBOARD
    let activeFilters = {
        line: "",
        startDate: "2025-12-02",
        endDate: "2025-12-08",
        regime: "", // Passo 1 obrigatório vazio inicialmente
        startHour: "00:00",
        endHour: "24:00",
        direction: "VOLTA"
    };

    // MAPAS LEAFLET E PARADAS
    let mapCongestion = null;
    let mapReplay = null;
    
    let congestionSegments = [];
    let congestionStopMarkers = [];
    let congestionRouteLine = null;

    let replayStopMarkers = [];
    let replayRouteLine = null;
    let replayBusMarkers = {}; // Mapeamento caseId -> L.Marker

    // DADOS HISTÓRICOS PARA REPLAY (MAP B)
    let replayTripsData = []; // Array de viagens com seus paths correspondentes
    let minTimeReplay = null; // Timestamp (Date) inicial das viagens
    let maxTimeReplay = null; // Timestamp (Date) final das viagens
    let currentReplayTime = null; // Timestamp (Date) atual da simulação
    let replayInterval = null; // Intervalo da animação (Timer)
    let isReplaying = false;

    // ELEMENTOS DOM
    const radioRegimes = document.getElementsByName("regime");
    const lockedContainer = document.getElementById("locked-filters-container");
    const selectLinha = document.getElementById("select-linha");
    const customDateInputs = document.getElementById("custom-date-inputs");
    const dateInicio = document.getElementById("date-inicio");
    const dateFim = document.getElementById("date-fim");
    const btnVerificar = document.getElementById("btn-verificar");
    const btnProcessar = document.getElementById("btn-processar");
    const chkPeriodoPersonalizado = document.getElementById("chk-periodo-personalizado");
    const logConsole = document.getElementById("log-console");

    // DUAL HOUR SLIDERS
    const hourSliderMin = document.getElementById("hour-slider-min");
    const hourSliderMax = document.getElementById("hour-slider-max");
    const hourRangeDisplay = document.getElementById("hour-range-display");

    // OUTROS ELEMENTOS DO FRONTEND
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanels = document.querySelectorAll(".tab-panel");
    const selectSentidoMapa = document.getElementById("select-sentido-mapa");
    const selectSentidoDescoberta = document.getElementById("select-sentido-descoberta");
    const selectSentidoConformidade = document.getElementById("select-sentido-conformidade");
    const selectSentidoDesempenho = document.getElementById("select-sentido-desempenho");

    // REPLAY CONTROLS (MAP B)
    const btnReplayPlay = document.getElementById("btn-replay-play");
    const timelineSlider = document.getElementById("timeline-slider");
    const replayTimeDisplay = document.getElementById("replay-time-display");
    const selectReplaySpeed = document.getElementById("select-replay-speed");

    // KPIS
    const kpiViagens = document.getElementById("kpi-viagens");
    const kpiEventos = document.getElementById("kpi-eventos");
    const kpiVeiculos = document.getElementById("kpi-veiculos");
    const kpiInterpolacao = document.getElementById("kpi-interpolacao");

    // ==========================================
    // ==========================================
    // PASSO 1: HIERARQUIA E DESBLOQUEIO DE REGIME
    // ==========================================
    Array.from(radioRegimes).forEach(radio => {
        radio.addEventListener("change", (e) => {
            const regimeVal = e.target.value;
            activeFilters.regime = regimeVal;

            // Desbloquear container visualmente
            lockedContainer.classList.add("unlocked");

            // Ativar inputs
            selectLinha.removeAttribute("disabled");
            hourSliderMin.removeAttribute("disabled");
            hourSliderMax.removeAttribute("disabled");
            dateInicio.removeAttribute("disabled");
            dateFim.removeAttribute("disabled");
            btnVerificar.removeAttribute("disabled");
            btnProcessar.removeAttribute("disabled");
            chkPeriodoPersonalizado.removeAttribute("disabled");

            const checkboxes = lockedContainer.querySelectorAll("input[type='checkbox']");
            checkboxes.forEach(chk => chk.removeAttribute("disabled"));

            // Ajustar datas conforme regime e checkbox personalizado
            if (chkPeriodoPersonalizado.checked) {
                customDateInputs.classList.remove("hidden");
                if (regimeVal === "A") {
                    dateInicio.value = "2025-10-24";
                    dateFim.value = "2025-10-30";
                } else if (regimeVal === "B") {
                    dateInicio.value = "2025-12-02";
                    dateFim.value = "2025-12-08";
                }
                activeFilters.startDate = dateInicio.value;
                activeFilters.endDate = dateFim.value;
            } else {
                customDateInputs.classList.add("hidden");
                if (regimeVal === "A") {
                    activeFilters.startDate = "2025-10-24";
                    activeFilters.endDate = "2025-10-30";
                } else if (regimeVal === "B") {
                    activeFilters.startDate = "2025-12-02";
                    activeFilters.endDate = "2025-12-08";
                }
            }

            // Atualizar console e buscar linhas
            logConsole.textContent = `Regime/Modo ${regimeVal} selecionado. Buscando linhas...\n`;
            loadCommonLines();
        });
    });

    // Ouvinte para checkbox de período personalizado
    chkPeriodoPersonalizado.addEventListener("change", (e) => {
        const isCustom = e.target.checked;
        if (isCustom) {
            customDateInputs.classList.remove("hidden");
            if (activeFilters.regime === "A") {
                dateInicio.value = "2025-10-24";
                dateFim.value = "2025-10-30";
            } else if (activeFilters.regime === "B") {
                dateInicio.value = "2025-12-02";
                dateFim.value = "2025-12-08";
            }
            activeFilters.startDate = dateInicio.value;
            activeFilters.endDate = dateFim.value;
        } else {
            customDateInputs.classList.add("hidden");
            if (activeFilters.regime === "A") {
                activeFilters.startDate = "2025-10-24";
                activeFilters.endDate = "2025-10-30";
            } else if (activeFilters.regime === "B") {
                activeFilters.startDate = "2025-12-02";
                activeFilters.endDate = "2025-12-08";
            }
        }
        logConsole.textContent += `Período personalizado ${isCustom ? 'ativado' : 'desativado'}. Datas: ${activeFilters.startDate} até ${activeFilters.endDate}\n`;
        logConsole.parentElement.scrollTop = logConsole.parentElement.scrollHeight;
        checkActiveLineData();
    });

    // Ouvintes para inputs de datas personalizadas
    dateInicio.addEventListener("change", (e) => {
        if (chkPeriodoPersonalizado.checked) {
            activeFilters.startDate = e.target.value;
            checkActiveLineData();
        }
    });
    dateFim.addEventListener("change", (e) => {
        if (chkPeriodoPersonalizado.checked) {
            activeFilters.endDate = e.target.value;
            checkActiveLineData();
        }
    });

    // ==========================================
    // BUSCAR LINHAS DE ÔNIBUS DISPONÍVEIS
    // ==========================================
    function loadCommonLines() {
        const previousLine = activeFilters.line;
        const regime = activeFilters.regime || "";
        fetch(`/api/lines?regime=${regime}`)
            .then(res => res.json())
            .then(data => {
                selectLinha.innerHTML = "";
                if (data.lines && data.lines.length > 0) {
                    data.lines.forEach(line => {
                        const option = document.createElement("option");
                        option.value = line;
                        option.textContent = line;
                        if (line === previousLine) {
                            option.selected = true;
                        }
                        selectLinha.appendChild(option);
                    });
                    
                    if (data.lines.includes(previousLine)) {
                        activeFilters.line = previousLine;
                    } else {
                        activeFilters.line = selectLinha.value;
                    }
                    logConsole.textContent += `Pronto! Selecione a linha e configure os filtros desejados.\n`;
                    
                    // Auto-verifica dados da linha ativa
                    checkActiveLineData();
                } else {
                    selectLinha.innerHTML = `<option value="">Nenhuma linha encontrada</option>`;
                    activeFilters.line = "";
                }
            })
            .catch(err => {
                console.error("Erro ao carregar linhas:", err);
                selectLinha.innerHTML = `<option value="">Erro ao carregar linhas</option>`;
            });
    }

    // Ouvinte de mudança da linha
    selectLinha.addEventListener("change", (e) => {
        activeFilters.line = e.target.value;
        logConsole.textContent += `Linha alterada para: ${activeFilters.line}\n`;
        logConsole.parentElement.scrollTop = logConsole.parentElement.scrollHeight;
        checkActiveLineData();
    });

    function checkActiveLineData() {
        if (!activeFilters.line) return;
        const sh = activeFilters.startHour;
        const eh = activeFilters.endHour;
        const checkUrl = `/api/check-trips?line=${activeFilters.line}&start_date=${activeFilters.startDate}&end_date=${activeFilters.endDate}&start_hour=${sh}&end_hour=${eh}`;
        
        fetch(checkUrl)
            .then(res => res.json())
            .then(data => {
                if (data.status === "processed" && data.exists) {
                    logConsole.textContent += `[INFO] Viagens processadas encontradas para a linha ${activeFilters.line}. Carregando visualizações...\n`;
                    refreshAllTabs();
                } else {
                    logConsole.textContent += `[AVISO] Dados não minerados para a linha ${activeFilters.line} neste período. Clique em "Processar Mineração" para gerar.\n`;
                    clearAllViews();
                }
                logConsole.parentElement.scrollTop = logConsole.parentElement.scrollHeight;
            })
            .catch(err => {
                console.error("Erro ao verificar dados da linha:", err);
            });
    }

    function clearAllViews() {
        stopReplaySimulation();
        
        // Limpar mapas
        congestionSegments.forEach(seg => { if (mapCongestion && seg) mapCongestion.removeLayer(seg); });
        congestionSegments = [];
        congestionStopMarkers.forEach(marker => { if (mapCongestion && marker) mapCongestion.removeLayer(marker); });
        congestionStopMarkers = [];
        if (congestionRouteLine && mapCongestion) {
            mapCongestion.removeLayer(congestionRouteLine);
            congestionRouteLine = null;
        }
        
        replayStopMarkers.forEach(marker => { if (mapReplay && marker) mapReplay.removeLayer(marker); });
        replayStopMarkers = [];
        Object.values(replayBusMarkers).forEach(marker => { if (mapReplay && marker) mapReplay.removeLayer(marker); });
        replayBusMarkers = {};
        if (replayRouteLine && mapReplay) {
            mapReplay.removeLayer(replayRouteLine);
            replayRouteLine = null;
        }
        
        // Reset KPIs
        kpiViagens.textContent = "---";
        kpiEventos.textContent = "---";
        kpiVeiculos.textContent = "---";
        kpiInterpolacao.textContent = "---";
        
        // Reset placeholders
        const petriContainer = document.getElementById("svg-descoberta-container");
        if (petriContainer) {
            petriContainer.innerHTML = `<div class="placeholder-msg">Nenhum dado minerado para esta linha. Execute a mineração.</div>`;
        }
        const perfContainer = document.getElementById("svg-desempenho-container");
        if (perfContainer) {
            perfContainer.innerHTML = `<div class="placeholder-msg">Nenhum dado minerado para esta linha. Execute a mineração.</div>`;
        }
    }

    // ==========================================
    // DUAL HOUR RANGE SLIDER
    // ==========================================
    function updateHourSliderValues() {
        let valMin = parseInt(hourSliderMin.value);
        let valMax = parseInt(hourSliderMax.value);

        // Prevenir cruzamento de sliders
        if (valMin >= valMax) {
            if (this === hourSliderMin) {
                hourSliderMin.value = valMax - 1;
                valMin = valMax - 1;
            } else {
                hourSliderMax.value = valMin + 1;
                valMax = valMin + 1;
            }
        }

        const strMin = String(valMin).padStart(2, '0') + ":00";
        // Formatar 24:00 como 23:59 para o datetime no python
        const strMax = valMax === 24 ? "23:59" : String(valMax).padStart(2, '0') + ":00";

        activeFilters.startHour = strMin;
        activeFilters.endHour = strMax;
        hourRangeDisplay.textContent = `${strMin} - ${valMax === 24 ? "24:00" : strMax}`;
    }

    hourSliderMin.addEventListener("input", updateHourSliderValues);
    hourSliderMax.addEventListener("input", updateHourSliderValues);
    hourSliderMin.addEventListener("change", refreshAllTabs);
    hourSliderMax.addEventListener("change", refreshAllTabs);

    // ==========================================
    // VERIFICAÇÃO DE VIAGENS ANTES DE MINAR
    // ==========================================
    btnVerificar.addEventListener("click", () => {
        if (!activeFilters.line) {
            alert("Selecione uma linha primeiro.");
            return;
        }

        const sh = activeFilters.startHour;
        const eh = activeFilters.endHour;

        logConsole.textContent += `\n[VERIFICAÇÃO] Procurando viagens para Linha ${activeFilters.line} entre ${sh} e ${eh === "23:59" ? "24:00" : eh}...\n`;
        logConsole.parentElement.scrollTop = logConsole.parentElement.scrollHeight;

        const checkUrl = `/api/check-trips?line=${activeFilters.line}&start_date=${activeFilters.startDate}&end_date=${activeFilters.endDate}&start_hour=${sh}&end_hour=${eh}`;

        fetch(checkUrl)
            .then(res => res.json())
            .then(data => {
                const msg = data.message || data.detail || JSON.stringify(data);
                logConsole.textContent += `[RESULTADO] ${msg}\n`;
                if (data.exists) {
                    logConsole.textContent += `Sucesso: Pronto para carregar! Clique em "Processar Mineração" para ativar os mapas.\n`;
                } else {
                    logConsole.textContent += `Aviso: Caso você processe agora, os mapas estarão vazios. Tente ampliar a faixa de horário ou mudar de regime.\n`;
                }
                logConsole.parentElement.scrollTop = logConsole.parentElement.scrollHeight;
            })
            .catch(err => {
                logConsole.textContent += `[ERRO] Falha ao consultar viagens: ${err.message}\n`;
                logConsole.parentElement.scrollTop = logConsole.parentElement.scrollHeight;
            });
    });

    // ==========================================
    // EXECUÇÃO DO PIPELINE DE MINERAÇÃO (SSE)
    // ==========================================
    btnProcessar.addEventListener("click", () => {
        if (!activeFilters.line) {
            alert("Selecione uma linha.");
            return;
        }

        logConsole.textContent = "";
        btnProcessar.disabled = true;
        btnProcessar.textContent = "Processando...";


        const sseUrl = `/api/process-stream?line=${activeFilters.line}&start_date=${activeFilters.startDate}&end_date=${activeFilters.endDate}`;
        const eventSource = new EventSource(sseUrl);

        eventSource.onmessage = (event) => {
            const data = event.data;
            if (data === "__SUCCESS__") {
                logConsole.textContent += "\n[SUCESSO] Processamento do log de eventos finalizado!\n";
                eventSource.close();
                btnProcessar.disabled = false;
                btnProcessar.textContent = "Processar Mineração";
                refreshAllTabs();
            } else if (data === "__FAILURE__") {
                logConsole.textContent += "\n[FALHA] Falha crítica no processamento.\n";
                eventSource.close();
                btnProcessar.disabled = false;
                btnProcessar.textContent = "Processar Mineração";
            } else {
                logConsole.textContent += data + "\n";
            }
            logConsole.parentElement.scrollTop = logConsole.parentElement.scrollHeight;
        };

        eventSource.onerror = (err) => {
            console.error("Erro no SSE:", err);
            logConsole.textContent += "\n[ERRO] Falha de comunicação com o servidor.\n";
            eventSource.close();
            btnProcessar.disabled = false;
            btnProcessar.textContent = "Processar Mineração";
        };
    });

    // ==========================================
    // REFRESH E NAVEGAÇÃO DE ABAS
    // ==========================================
    function refreshAllTabs() {
        const activeTabBtn = document.querySelector(".tab-btn.active");
        const activeTabId = activeTabBtn.getAttribute("data-tab");
        loadTabData(activeTabId);
    }

    function loadTabData(tabId) {
        // Obter filtros de horários
        const sh = activeFilters.startHour;
        const eh = activeFilters.endHour;

        if (tabId === "tab-mapa") {
            loadMapsAndMetrics(selectSentidoMapa.value, sh, eh);
        } else if (tabId === "tab-descoberta") {
            loadDiscoveryGraph(selectSentidoDescoberta.value, sh, eh);
        } else if (tabId === "tab-conformidade") {
            loadConformanceMetrics(selectSentidoConformidade.value, sh, eh);
        } else if (tabId === "tab-desempenho") {
            loadPerformanceGraph(selectSentidoDesempenho.value, sh, eh);
        }
    }

    // Ouvintes dos sentidos
    selectSentidoMapa.addEventListener("change", (e) => loadMapsAndMetrics(e.target.value, activeFilters.startHour, activeFilters.endHour));
    selectSentidoDescoberta.addEventListener("change", (e) => loadDiscoveryGraph(e.target.value, activeFilters.startHour, activeFilters.endHour));
    selectSentidoConformidade.addEventListener("change", (e) => loadConformanceMetrics(e.target.value, activeFilters.startHour, activeFilters.endHour));
    selectSentidoDesempenho.addEventListener("change", (e) => loadPerformanceGraph(e.target.value, activeFilters.startHour, activeFilters.endHour));

    // Navegação de abas
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const targetTab = btn.getAttribute("data-tab");
            tabPanels.forEach(panel => {
                if (panel.id === targetTab) panel.classList.add("active");
                else panel.classList.remove("active");
            });

            loadTabData(targetTab);
        });
    });

    // ==========================================
    // IMPLEMENTAÇÃO DOS MAPAS (MAP A E MAP B)
    // ==========================================
    function loadMapsAndMetrics(direction, sh, eh) {
        activeFilters.direction = direction;
        
        // Parar animações e replays ativos
        stopReplaySimulation();

        const url = `/api/map-data?line=${activeFilters.line}&start_date=${activeFilters.startDate}&end_date=${activeFilters.endDate}&direction=${direction}&start_hour=${sh}&end_hour=${eh}`;

        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error("Dados não encontrados. Processe a mineração primeiro.");
                return res.json();
            })
            .then(data => {
                // KPIs
                if (data.metrics) {
                    kpiViagens.textContent = data.metrics.total_viagens;
                    kpiEventos.textContent = data.metrics.total_eventos;
                    kpiVeiculos.textContent = data.metrics.veiculos_ativos;
                    kpiInterpolacao.textContent = data.metrics.taxa_interpolacao.toFixed(1) + "%";
                }

                // Renderizar Mapas A e B
                renderMaps(data.stops, data.shape, data.segments, data.replay_trips);
            })
            .catch(err => {
                console.error(err);
                logConsole.textContent += `\n[MAPA] ${err.message}\n`;
            });
    }

    function renderMaps(stops, shape, segments, replayTrips) {
        // 1. INICIALIZAR MAP CONGESTION (MAP A)
        if (!mapCongestion) {
            mapCongestion = L.map('map-congestion').setView([-25.43, -49.27], 13);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO'
            }).addTo(mapCongestion);
        }

        // 2. INICIALIZAR MAP REPLAY (MAP B)
        if (!mapReplay) {
            mapReplay = L.map('map-replay').setView([-25.43, -49.27], 13);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO'
            }).addTo(mapReplay);
            
            // Sincronizar panners
            mapCongestion.on('drag', () => mapReplay.setView(mapCongestion.getCenter(), mapCongestion.getZoom(), {animate: false}));
            mapCongestion.on('zoom', () => mapReplay.setZoom(mapCongestion.getZoom()));
        }

        // LIMPAR ANTERIORES - MAP A (Congestionamento)
        congestionSegments.forEach(seg => mapCongestion.removeLayer(seg));
        congestionSegments = [];
        congestionStopMarkers.forEach(marker => mapCongestion.removeLayer(marker));
        congestionStopMarkers = [];
        if (congestionRouteLine) {
            mapCongestion.removeLayer(congestionRouteLine);
            congestionRouteLine = null;
        }

        // LIMPAR ANTERIORES - MAP B (Replay)
        replayStopMarkers.forEach(marker => mapReplay.removeLayer(marker));
        replayStopMarkers = [];
        Object.values(replayBusMarkers).forEach(marker => mapReplay.removeLayer(marker));
        replayBusMarkers = {};
        if (replayRouteLine) {
            mapReplay.removeLayer(replayRouteLine);
            replayRouteLine = null;
        }

        // ROTA TEÓRICA DE FUNDO
        if (shape && shape.length > 0) {
            congestionRouteLine = L.polyline(shape, { color: '#475569', weight: 2, opacity: 0.3, dashArray: '5, 5' }).addTo(mapCongestion);
            replayRouteLine = L.polyline(shape, { color: '#475569', weight: 2, opacity: 0.3, dashArray: '5, 5' }).addTo(mapReplay);
            mapCongestion.fitBounds(congestionRouteLine.getBounds(), { padding: [20, 20] });
        }

        // PARADAS CIRCULARES - HOVER TOOLTIP
        const makeStopMarkers = (stopList, leafletMap, markersStorage) => {
            stopList.forEach(stop => {
                const marker = L.circleMarker([stop.lat, stop.lon], {
                    radius: 5,
                    fillColor: '#ff758c',
                    color: '#ff4b4b',
                    weight: 1,
                    fillOpacity: 0.9
                }).addTo(leafletMap);

                const htmlTooltip = `
                    <div style="font-family: 'Inter', sans-serif; font-size: 11px; color: #f1f5f9; width: 180px; padding: 4px;">
                        <h4 style="margin: 0 0 3px 0; font-size: 12px; font-weight: 700; color: #ffffff;">Seq ${stop.seq}: ${stop.nome}</h4>
                        <p style="margin: 0; color: #94a3b8; font-size: 10px;">Código: ${stop.num}</p>
                        <hr style="border-top: 1px solid #334155; margin: 5px 0;"/>
                        <table style="width: 100%;">
                            <tr><td>Passagens:</td><td style="text-align: right; color: #39e587; font-weight:700;">${stop.passages}</td></tr>
                            <tr><td>Interpolado:</td><td style="text-align: right; color: ${stop.interpolated ? '#ff4b4b' : '#3b82f6'}; font-weight:700;">${stop.interpolated ? 'Sim' : 'Não'}</td></tr>
                        </table>
                    </div>
                `;
                marker.bindTooltip(htmlTooltip, { direction: 'top', className: 'custom-map-tooltip', sticky: true });
                markersStorage.push(marker);
            });
        };

        makeStopMarkers(stops, mapCongestion, congestionStopMarkers);
        makeStopMarkers(stops, mapReplay, replayStopMarkers);

        // MAPA A: TRECHOS COLORIDOS POR VELOCIDADE MÉDIA
        if (segments && segments.length > 0) {
            segments.forEach(seg => {
                const pl = L.polyline(seg.coords, {
                    color: seg.color,
                    weight: 4.5,
                    opacity: 0.9,
                    lineJoin: 'round'
                }).addTo(mapCongestion);

                const tooltipSpeed = `
                    <div style="font-family: 'Inter', sans-serif; font-size: 11px; color: #f1f5f9; padding: 2px;">
                        <strong>Trecho:</strong> ${seg.from_stop} &rarr; ${seg.to_stop}<br/>
                        <strong>Velocidade Média:</strong> <span style="color:${seg.color}; font-weight:700;">${seg.speed.toFixed(1)} km/h</span>
                    </div>
                `;
                pl.bindTooltip(tooltipSpeed, { sticky: true });
                congestionSegments.push(pl);
            });
        }

        // MAPA B: PREPARAR OS DADOS DO REPLAY DE FROTAS
        replayTripsData = replayTrips;
        setupReplayTimeline();
    }

    // ==========================================
    // MOTOR DE REPLAY DA FROTA (SIMULADOR MAP B)
    // ==========================================
    function setupReplayTimeline() {
        if (replayTripsData.length === 0) {
            timelineSlider.value = 0;
            timelineSlider.disabled = true;
            btnReplayPlay.disabled = true;
            replayTimeDisplay.textContent = "Sem viagens ativas";
            return;
        }

        timelineSlider.disabled = false;
        btnReplayPlay.disabled = false;

        // Descobrir a menor e maior data da janela horária ativa
        let allTimes = [];
        replayTripsData.forEach(trip => {
            trip.path.forEach(pt => {
                allTimes.push(new Date(pt.time));
            });
        });

        // Ordenar os tempos para obter min e max
        allTimes.sort((a, b) => a - b);
        minTimeReplay = allTimes[0];
        maxTimeReplay = allTimes[allTimes.length - 1];

        currentReplayTime = new Date(minTimeReplay.getTime());
        timelineSlider.value = 0;
        updateReplayTimeDisplay();

        // Limpar marcadores de ônibus antigos
        Object.values(replayBusMarkers).forEach(m => mapReplay.removeLayer(m));
        replayBusMarkers = {};
    }

    function updateReplayTimeDisplay() {
        if (!currentReplayTime) return;
        
        // Exibir formato HH:MM:SS
        const h = String(currentReplayTime.getHours()).padStart(2, '0');
        const m = String(currentReplayTime.getMinutes()).padStart(2, '0');
        const s = String(currentReplayTime.getSeconds()).padStart(2, '0');
        replayTimeDisplay.textContent = `${h}:${m}:${s}`;
    }

    function updateBusesPositions() {
        if (!currentReplayTime || replayTripsData.length === 0) return;

        replayTripsData.forEach(trip => {
            const path = trip.path;
            
            // Achar o segmento onde o ônibus estaria neste exato timestamp
            let p1 = null;
            let p2 = null;

            for (let i = 0; i < path.length - 1; i++) {
                const t1 = new Date(path[i].time);
                const t2 = new Date(path[i+1].time);

                if (currentReplayTime >= t1 && currentReplayTime <= t2) {
                    p1 = path[i];
                    p2 = path[i+1];
                    break;
                }
            }

            if (p1 && p2) {
                // Interpolação linear do tempo
                const t1Ms = new Date(p1.time).getTime();
                const t2Ms = new Date(p2.time).getTime();
                const curMs = currentReplayTime.getTime();

                const ratio = (curMs - t1Ms) / (t2Ms - t1Ms);

                // Calcular latitude/longitude interpoladas
                const lat = p1.lat + (p2.lat - p1.lat) * ratio;
                const lon = p1.lon + (p2.lon - p1.lon) * ratio;

                // Desenhar ou mover marcador do ônibus
                if (!replayBusMarkers[trip.case_id]) {
                    const busIcon = L.divIcon({
                        html: '<div class="bus-animation-icon">🚌</div>',
                        className: 'custom-bus-icon',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    });
                    
                    const m = L.marker([lat, lon], { icon: busIcon }).addTo(mapReplay);
                    m.bindTooltip(`<strong>Prefixo:</strong> ${trip.vehicle}<br/><strong>Próximo ponto:</strong> ${p2.stop_name}`);
                    replayBusMarkers[trip.case_id] = m;
                } else {
                    replayBusMarkers[trip.case_id].setLatLng([lat, lon]);
                }
            } else {
                // Ônibus fora da janela de horário atual (remover do mapa)
                if (replayBusMarkers[trip.case_id]) {
                    mapReplay.removeLayer(replayBusMarkers[trip.case_id]);
                    delete replayBusMarkers[trip.case_id];
                }
            }
        });
    }

    function playReplay() {
        if (isReplaying) return;
        isReplaying = true;
        btnReplayPlay.textContent = "⏸ Pause";

        const speedMultiplier = parseInt(selectReplaySpeed.value);

        replayInterval = setInterval(() => {
            // Incrementar tempo de replay (ex: 1 segundo real * multiplicador)
            currentReplayTime = new Date(currentReplayTime.getTime() + (1000 * speedMultiplier));

            if (currentReplayTime >= maxTimeReplay) {
                currentReplayTime = new Date(maxTimeReplay.getTime());
                stopReplaySimulation();
            }

            // Atualizar slider da timeline
            const totalMs = maxTimeReplay.getTime() - minTimeReplay.getTime();
            const curMs = currentReplayTime.getTime() - minTimeReplay.getTime();
            timelineSlider.value = (curMs / totalMs) * 100;

            updateReplayTimeDisplay();
            updateBusesPositions();
        }, 100); // 10 ticks por segundo
    }

    function pauseReplay() {
        isReplaying = false;
        btnReplayPlay.textContent = "▶ Play";
        if (replayInterval) {
            clearInterval(replayInterval);
            replayInterval = null;
        }
    }

    function stopReplaySimulation() {
        pauseReplay();
        // Limpar ônibus ativos do mapa B
        Object.values(replayBusMarkers).forEach(m => mapReplay.removeLayer(m));
        replayBusMarkers = {};
    }

    // Clique do Play/Pause
    btnReplayPlay.onclick = () => {
        if (isReplaying) {
            pauseReplay();
        } else {
            playReplay();
        }
    };

    // Arrastar slider da timeline
    timelineSlider.addEventListener("input", () => {
        pauseReplay();
        if (!minTimeReplay || !maxTimeReplay) return;

        const ratio = parseFloat(timelineSlider.value) / 100;
        const totalMs = maxTimeReplay.getTime() - minTimeReplay.getTime();
        
        currentReplayTime = new Date(minTimeReplay.getTime() + (totalMs * ratio));
        updateReplayTimeDisplay();
        updateBusesPositions();
    });

    // Mudar multiplicador de velocidade no meio da simulação
    selectReplaySpeed.onchange = () => {
        if (isReplaying) {
            pauseReplay();
            playReplay();
        }
    };

    // ==========================================
    // MÉTODOS DE RENDERIZAÇÃO DAS OUTRAS ABAS
    // ==========================================
    
    // Aba 2: Descoberta de Processos (Rede de Petri)
    function loadDiscoveryGraph(direction, sh, eh) {
        const url = `/api/discovery?line=${activeFilters.line}&start_date=${activeFilters.startDate}&end_date=${activeFilters.endDate}&direction=${direction}&start_hour=${sh}&end_hour=${eh}`;
        const container = document.getElementById("svg-descoberta-container");
        container.innerHTML = '<div class="placeholder-msg">Carregando Rede de Petri...</div>';

        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error("Erro ao gerar SVG.");
                return res.text();
            })
            .then(svgText => {
                container.innerHTML = svgText;
                setupSvgInteractivity("viewport-descoberta", "svg-descoberta-container");
            })
            .catch(err => {
                container.innerHTML = `<div class="placeholder-msg" style="color:#ff4b4b;">Sem dados para este período de hora.</div>`;
            });
    }

    // Aba 3: Auditoria & Conformidade
    function loadConformanceMetrics(direction, sh, eh) {
        const url = `/api/conformance?line=${activeFilters.line}&start_date=${activeFilters.startDate}&end_date=${activeFilters.endDate}&direction=${direction}&start_hour=${sh}&end_hour=${eh}`;
        const valAvgFitness = document.getElementById("val-avg-fitness");
        const valFitPct = document.getElementById("val-fit-pct");
        const tableSkippedBody = document.querySelector("#table-skipped-stops tbody");
        const tableDeviantBody = document.querySelector("#table-deviant-trips tbody");

        valAvgFitness.textContent = "Carregando...";
        valFitPct.textContent = "Carregando...";
        tableSkippedBody.innerHTML = '<tr><td colspan="2" class="empty-table">Carregando...</td></tr>';
        tableDeviantBody.innerHTML = '<tr><td colspan="5" class="empty-table">Carregando...</td></tr>';

        fetch(url)
            .then(res => res.json())
            .then(data => {
                valAvgFitness.textContent = data.avg_fitness.toFixed(3);
                valFitPct.textContent = data.fit_percentage.toFixed(1) + "%";

                tableSkippedBody.innerHTML = "";
                if (data.skipped_stops && data.skipped_stops.length > 0) {
                    data.skipped_stops.forEach(item => {
                        const tr = document.createElement("tr");
                        tr.innerHTML = `<td>${item.stop_name}</td><td><span class="table-badge-red">${item.count} vezes</span></td>`;
                        tableSkippedBody.appendChild(tr);
                    });
                } else {
                    tableSkippedBody.innerHTML = '<tr><td colspan="2" class="empty-table" style="color: #39e587;">Nenhuma parada pulada!</td></tr>';
                }

                tableDeviantBody.innerHTML = "";
                if (data.deviant_trips && data.deviant_trips.length > 0) {
                    data.deviant_trips.forEach(trip => {
                        const tr = document.createElement("tr");
                        tr.innerHTML = `<td>${trip.case_id}</td><td>${trip.vehicle}</td><td>${trip.tabela}</td><td><span class="table-badge-red">${trip.skipped_count} pts</span></td><td><span class="table-badge-blue">${trip.interpolated_count} pts</span></td>`;
                        tableDeviantBody.appendChild(tr);
                    });
                } else {
                    tableDeviantBody.innerHTML = '<tr><td colspan="5" class="empty-table">Sem registros de desvios no período.</td></tr>';
                }
            })
            .catch(() => {
                valAvgFitness.textContent = "Erro";
                valFitPct.textContent = "Erro";
                tableSkippedBody.innerHTML = '<tr><td colspan="2" class="empty-table" style="color:#ff4b4b;">Erro</td></tr>';
                tableDeviantBody.innerHTML = '<tr><td colspan="5" class="empty-table" style="color:#ff4b4b;">Erro</td></tr>';
            });
    }

    // Aba 4: Desempenho & Gargalos (Performance DFG)
    function loadPerformanceGraph(direction, sh, eh) {
        const url = `/api/performance?line=${activeFilters.line}&start_date=${activeFilters.startDate}&end_date=${activeFilters.endDate}&direction=${direction}&start_hour=${sh}&end_hour=${eh}`;
        const container = document.getElementById("svg-desempenho-container");
        container.innerHTML = '<div class="placeholder-msg">Carregando Fluxo DFG...</div>';

        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error("Erro ao gerar DFG.");
                return res.text();
            })
            .then(svgText => {
                container.innerHTML = svgText;
                setupSvgInteractivity("viewport-desempenho", "svg-desempenho-container");
            })
            .catch(() => {
                container.innerHTML = `<div class="placeholder-msg" style="color:#ff4b4b;">Sem dados para este período de hora.</div>`;
            });
    }

    // CONTROLE DE INTERATIVIDADE DO SVG (ZOOM & PAN DRAG)
    function setupSvgInteractivity(viewportId, containerId) {
        const viewport = document.getElementById(viewportId);
        const container = document.getElementById(containerId);
        const svg = container.querySelector("svg");
        if (!svg) return;

        let scale = 1.0;
        let isDragging = false;
        let startX = 0, startY = 0;
        let translateX = 0, translateY = 0;

        container.style.transform = `translate(0px, 0px) scale(1)`;

        viewport.onwheel = (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? -0.1 : 0.1;
            scale = Math.max(0.2, Math.min(4.0, scale + delta));
            container.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
        };

        viewport.onmousedown = (e) => {
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
        };

        window.onmousemove = (e) => {
            if (!isDragging) return;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            container.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
        };

        window.onmouseup = () => {
            isDragging = false;
        };

        // Botoes zoom/reset
        const zoomInBtn = viewportId === "viewport-descoberta" ? document.getElementById("btn-zoom-in-desc") : document.getElementById("btn-zoom-in-des");
        const zoomOutBtn = viewportId === "viewport-descoberta" ? document.getElementById("btn-zoom-out-desc") : document.getElementById("btn-zoom-out-des");
        const resetBtn = viewportId === "viewport-descoberta" ? document.getElementById("btn-reset-desc") : document.getElementById("btn-reset-des");

        if (zoomInBtn) {
            zoomInBtn.onclick = () => { scale = Math.min(4.0, scale + 0.15); container.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`; };
        }
        if (zoomOutBtn) {
            zoomOutBtn.onclick = () => { scale = Math.max(0.2, scale - 0.15); container.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`; };
        }
        if (resetBtn) {
            resetBtn.onclick = () => { scale = 1.0; translateX = 0; translateY = 0; container.style.transform = `translate(0px, 0px) scale(1)`; };
        }
    }
});

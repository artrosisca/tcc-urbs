import React, { useState, useEffect, useRef } from 'react';
import DeckGL from '@deck.gl/react';
import { MapView } from '@deck.gl/core';
import { TileLayer } from '@deck.gl/geo-layers';
import { PathLayer, ScatterplotLayer, IconLayer, BitmapLayer } from '@deck.gl/layers';
import { TripsLayer } from '@deck.gl/geo-layers';
import { X, Play, Pause, Compass, MapPin, Bus, Calendar, Activity, CheckCircle2, Clock, RotateCw } from 'lucide-react';

const LINE_ARCHETYPES = {
  '010': 'Interbairros I (Circular)',
  '541': 'Bairro Novo A (Alimentador)',
  '542': 'Bairro Novo B (Alimentador)',
  '500': 'Ligeirinho Boqueirão',
  '203': 'Santa Cândida / Capão Raso',
  '303': 'Centenário / Campo Comprido'
};

function formatDisplayPeriod(startDate, endDate) {
  if (!startDate) return '';
  const toBr = (iso) => {
    if (!iso || !iso.includes('-')) return iso;
    const parts = iso.split('-');
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  };
  if (!endDate || startDate === endDate) {
    return toBr(startDate);
  }
  return `${toBr(startDate)} a ${toBr(endDate)}`;
}

export default function GeospatialConsole({ mapData, isLogicalMode, setIsLogicalMode, isLoading, filters, activeTripId, onClearTrip }) {
  const [viewState, setViewState] = useState({
    longitude: -49.2768, // Curitiba
    latitude: -25.4311,
    zoom: 12,
    pitch: 30,
    bearing: 0,
    maxZoom: 20,
    minZoom: 9
  });

  // Time controls
  const [isPlaying, setIsPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [maxTime, setMaxTime] = useState(86400);
  const [minTime, setMinTime] = useState(0); // 24h in seconds
  const animationRef = useRef(null);

  // Extract paths for TripsLayer
  const [trips, setTrips] = useState([]);
  const [rawStops, setRawStops] = useState([]);
  const [shapeLine, setShapeLine] = useState([]);

  // Active metadata & staleness detection
  const meta = mapData?.metadata;
  const activeLine = meta?.line || filters?.line || '541';
  const activeDirection = meta?.direction || filters?.direction || 'VOLTA';
  const activeStartDate = meta?.start_date || filters?.startDate || '';
  const activeEndDate = meta?.end_date || filters?.endDate || '';
  const displayRegime = meta?.regime || (filters?.regime?.includes('20s') || filters?.regime?.includes('B') ? 'B' : 'A');

  const isDirectionMismatch = Boolean(
    filters?.direction &&
    meta?.direction &&
    meta.direction !== 'CIRCULAR' &&
    meta.direction !== filters.direction
  );

  const isDataStale = Boolean(
    filters && meta && (
      (filters.line && meta.line !== filters.line) ||
      isDirectionMismatch ||
      (filters.startDate && meta.start_date !== filters.startDate) ||
      (filters.endDate && meta.end_date !== filters.endDate)
    )
  );

  const totalStopsCount = mapData?.stops?.length ?? rawStops.length;
  const totalTripsCount = mapData?.metrics?.total_viagens ?? trips.length;

  useEffect(() => {
    if (!mapData) return;

    // Set stops
    if (mapData.stops) {
      setRawStops(mapData.stops);
      // Center map around the middle stop
      if (mapData.stops.length > 0) {
        const midStop = mapData.stops[Math.floor(mapData.stops.length / 2)];
        setViewState(prev => ({
          ...prev,
          longitude: midStop.lon,
          latitude: midStop.lat,
          zoom: 13
        }));
      }
    }

    // Set shape line
    if (mapData.shape) {
      setShapeLine(mapData.shape.map(p => Array.isArray(p) ? [p[1], p[0]] : [p.lon, p.lat]));
    }

    // Process trips for replay
    if (mapData.replay_trips) {
      const processedTrips = [];
      let minTimeVal = Infinity;
      let maxTimeVal = -Infinity;

      // Handle both array and object formats of replay_trips
      const tripsArray = Array.isArray(mapData.replay_trips) 
        ? mapData.replay_trips 
        : Object.entries(mapData.replay_trips).map(([id, pts]) => ({ case_id: id, path: pts }));

      tripsArray.forEach(trip => {
        const tripPoints = trip.path;
        if (!tripPoints || tripPoints.length < 2) return;

        const path = [];
        tripPoints.forEach(pt => {
          // Parse timestamp to seconds in day (handle 'time' or 'timestamp')
          const timeStr = pt.time || pt.timestamp;
          if (!timeStr) return;
          
          const ts = new Date(timeStr);
          if (isNaN(ts.getTime())) return; // skip invalid dates
          
          const secs = ts.getHours() * 3600 + ts.getMinutes() * 60 + ts.getSeconds();
          
          minTimeVal = Math.min(minTimeVal, secs);
          maxTimeVal = Math.max(maxTimeVal, secs);

          // Position depends on mode
          const lat = isLogicalMode ? (pt.mapped_lat || pt.lat) : pt.lat;
          const lon = isLogicalMode ? (pt.mapped_lon || pt.lon) : pt.lon;

          path.push({
            coordinate: [lon, lat],
            timestamp: secs,
            speed: pt.speed || 30.0
          });
        });

        if (path.length > 0) {
          processedTrips.push({
            id: trip.case_id || trip.id,
            path: path.map(p => p.coordinate),
            timestamps: path.map(p => p.timestamp),
            speeds: path.map(p => p.speed)
          });
        }
      });

      setTrips(processedTrips);

      if (activeTripId) {
        const singleTrip = processedTrips.find(t => t.id === activeTripId);
        if (singleTrip) {
          setTrips([singleTrip]);
          const t_min = Math.min(...singleTrip.timestamps);
          const t_max = Math.max(...singleTrip.timestamps);
          setTime(t_min);
          setMinTime(t_min);
          setMaxTime(t_max);
        }
      } else {
        if (minTimeVal !== Infinity) {
          setTime(minTimeVal);
          setMinTime(minTimeVal);
          setMaxTime(maxTimeVal);
        }
      }
    }
  }, [mapData, isLogicalMode, activeTripId]);

  // Animation Loop
  useEffect(() => {
    if (isPlaying) {
      const animate = () => {
        setTime(t => {
          if (t >= maxTime) {
            setIsPlaying(false);
            return maxTime;
          }
          return t + 2; // Speed multiplier (2 seconds per frame)
        });
        animationRef.current = requestAnimationFrame(animate);
      };
      animationRef.current = requestAnimationFrame(animate);
    } else if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [isPlaying, maxTime]);

  const handleTimeSliderChange = (e) => {
    setTime(parseInt(e.target.value));
  };

  const formatSeconds = (totalSecs) => {
    const hrs = Math.floor(totalSecs / 3600).toString().padStart(2, '0');
    const mins = Math.floor((totalSecs % 3600) / 60).toString().padStart(2, '0');
    const secs = (totalSecs % 60).toString().padStart(2, '0');
    return `${hrs}:${mins}:${secs}`;
  };

  // Deck.gl layers setup
  const layers = [
    // 1. Tile layer for map base (OpenStreetMap / CartoDB base tiles - cartocdn / openstreetmap attribution)
    new TileLayer({
      id: 'base-tiles',
      data: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      minZoom: 0,
      maxZoom: 19,
      tileSize: 256,
      renderSubLayers: props => {
        const { bbox } = props.tile;
        if (!bbox) return null;
        const { west, south, east, north } = bbox;
        return new BitmapLayer(props, {
          data: null,
          image: props.data,
          bounds: [west, south, east, north]
        });
      }
    }),

    // 2. Predefined shape line
    new PathLayer({
      id: 'shape-line-layer',
      data: [shapeLine],
      getPath: d => d,
      getColor: [59, 130, 246, 120], // Light blue
      getWidth: 4,
      widthMinPixels: 2,
      pickable: false
    }),

    // 3. Stop points
    new ScatterplotLayer({
      id: 'stops-points-layer',
      data: rawStops,
      getPosition: d => [d.lon, d.lat],
      getRadius: 15,
      getFillColor: [15, 23, 42, 225], // Dark slate
      getLineColor: [255, 255, 255, 255],
      getLineWidth: 2,
      lineWidthMinPixels: 1,
      pickable: true,
      onHover: info => {
        // Handle tooltip
      }
    }),

    // 4. TripsLayer to animate buses
    new TripsLayer({
      id: 'trips-animation-layer',
      data: trips,
      getPath: d => d.path,
      getTimestamps: d => d.timestamps,
      getColor: d => {
        // Red for deviant/non-conformant, Blue for normal
        return isLogicalMode ? [59, 130, 246, 255] : [239, 68, 68, 255];
      },
      opacity: 0.8,
      widthMinPixels: 5,
      rounded: true,
      trailLength: 120, // tail length in seconds
      currentTime: time,
      shadowEnabled: false
    }),

    // 5. Markers for current bus locations
    new ScatterplotLayer({
      id: 'buses-markers-layer',
      data: trips.map(t => {
        // Find index of current timestamp
        let idx = t.timestamps.findIndex(ts => ts >= time);
        if (idx === -1) idx = t.path.length - 1;
        return {
          id: t.id,
          coord: t.path[idx] || [-49.2768, -25.4311]
        };
      }),
      getPosition: d => d.coord,
      getRadius: 30,
      getFillColor: isLogicalMode ? [37, 99, 235, 255] : [220, 38, 38, 255], // Blue or Red
      getLineColor: [255, 255, 255, 255],
      getLineWidth: 3,
      lineWidthMinPixels: 2,
      pickable: true
    })
  ];

  return (
    <div className="relative w-full h-full bg-slate-100 flex flex-col">
      {/* Map Area */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50">
            <div className="bg-white p-5 rounded-xl shadow-lg border border-slate-150 flex flex-col items-center gap-3">
              <div className="h-8 w-8 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
              <span className="text-xs font-bold text-slate-600">Carregando mapa e dados...</span>
            </div>
          </div>
        )}
        <DeckGL
          viewState={viewState}
          onViewStateChange={e => setViewState(e.viewState)}
          controller={true}
          layers={layers}
          views={new MapView({ id: 'mapbox-view', repeat: true })}
        />
        
        {/* Toggle Mode Panel (Replay Dual) */}
        <div className="absolute top-4 left-4 bg-white/95 backdrop-blur shadow-md rounded-lg p-3 border border-slate-200 z-10 space-y-2">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Replay Dual (Validação)
          </div>
          <div className="flex gap-1.5 bg-slate-100 p-0.5 rounded-md">
            <button
              type="button"
              onClick={() => setIsLogicalMode(true)}
              className={`py-1.5 px-3 rounded-md text-xs font-semibold transition-all ${
                isLogicalMode
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Lógico (Alinhado)
            </button>
            <button
              type="button"
              onClick={() => setIsLogicalMode(false)}
              className={`py-1.5 px-3 rounded-md text-xs font-semibold transition-all ${
                !isLogicalMode
                  ? 'bg-white text-rose-600 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Físico (Real GPS)
            </button>
          </div>
        </div>

        {/* Floating Active Configuration & Sync Status Chip */}
        <div className="absolute top-4 right-4 bg-white/95 backdrop-blur shadow-md rounded-xl p-3 border border-slate-200/90 z-20 max-w-sm space-y-2 select-none">
          {/* Header row: Status indicator + Regime badge */}
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
                {isLoading || isDataStale ? (
                  <>
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
                  </>
                ) : (
                  <>
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </>
                )}
              </span>
              <span className="font-bold tracking-tight text-slate-700 text-xs flex items-center gap-1.5">
                {isLoading ? (
                  <>
                    <RotateCw className="h-3 w-3 animate-spin text-amber-600" />
                    <span>Carregando mapa...</span>
                  </>
                ) : isDataStale ? (
                  <>
                    <RotateCw className="h-3 w-3 animate-spin text-amber-600" />
                    <span>Sincronizando com filtros...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Mapa Sincronizado</span>
                  </>
                )}
              </span>
            </div>

            <span
              className={`px-2 py-0.5 rounded text-[10px] font-extrabold tracking-wider uppercase ${
                displayRegime === 'B'
                  ? 'bg-indigo-100 text-indigo-700 border border-indigo-200/70'
                  : 'bg-amber-100 text-amber-800 border border-amber-200/70'
              }`}
            >
              {displayRegime === 'B' ? 'Regime B (20s)' : 'Regime A (2m)'}
            </span>
          </div>

          {/* Line & Direction row */}
          <div className="flex items-center gap-1.5 border-t border-slate-100 pt-2">
            <Bus className="h-3.5 w-3.5 text-slate-500 flex-shrink-0" />
            <span className="font-extrabold text-slate-800 text-xs">
              Linha {activeLine}
            </span>
            <span className="text-slate-300">•</span>
            <span className="font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded text-[10px]">
              {activeDirection}
            </span>
            {LINE_ARCHETYPES[activeLine] && (
              <span className="text-slate-400 text-[10px] truncate max-w-[130px]" title={LINE_ARCHETYPES[activeLine]}>
                {LINE_ARCHETYPES[activeLine]}
              </span>
            )}
          </div>

          {/* Period & counts row */}
          <div className="flex items-center justify-between text-[11px] text-slate-500 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-150/60">
            <div className="flex items-center gap-1 font-medium">
              <Calendar className="h-3 w-3 text-slate-400 flex-shrink-0" />
              <span className="text-[10px]">{formatDisplayPeriod(activeStartDate, activeEndDate)}</span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-600">
              <span>{totalStopsCount} paradas</span>
              <span>•</span>
              <span>{totalTripsCount} viagens</span>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-24 right-4 bg-white/95 backdrop-blur shadow-md rounded-lg p-3 border border-slate-200 z-10 text-xs space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-slate-900 border border-white"></span>
            <span className="text-slate-600 font-medium">Ponto de Parada</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-3.5 h-1.5 rounded-full ${isLogicalMode ? 'bg-blue-500' : 'bg-red-500'}`}></span>
            <span className="text-slate-600 font-medium">Ônibus ({isLogicalMode ? 'Alinhado' : 'Real'})</span>
          </div>
        </div>
      </div>

      {/* Replay Controls Panel */}
      <div className="h-20 bg-white border-t border-slate-200 flex items-center px-6 gap-6 z-10">
        <button
          type="button"
          onClick={() => setIsPlaying(!isPlaying)}
          className="h-10 w-10 rounded-full bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 transition-all shadow-sm"
        >
          {isPlaying ? (
            <Pause className="h-4.5 w-4.5 fill-current" />
          ) : (
            <Play className="h-4.5 w-4.5 fill-current translate-x-0.5" />
          )}
        </button>

        {/* Timeline Slider */}
        <div className="flex-1 flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span className="flex items-center gap-1">
              <Compass className="h-3.5 w-3.5 animate-spin-slow" />
              <span>Linha do Tempo</span>
            </span>
            <span className="font-mono text-slate-700 bg-slate-100 py-0.5 px-2 rounded-md font-bold">
              {formatSeconds(time)}
            </span>
          </div>
          <input
            type="range"
            min={minTime}
            max={maxTime}
            value={time}
            onChange={handleTimeSliderChange}
            className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-slate-900 outline-none"
          />
        </div>
      </div>
    </div>
  );
}

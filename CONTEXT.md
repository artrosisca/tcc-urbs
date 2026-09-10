# URBS Process Mining Domain

Domain concepts and ubiquitous language for the URBS public transit process mining and performance analysis platform.

## Language

### Core Entities

**Event Log**:
The consolidated, chronologically ordered sequence of timestamped bus passage events grouped into discrete trips for process mining.
_Avoid_: Raw log, history, telemetry dump

**Trip (Viagem)**:
A single continuous directional traversal of a bus route by an operational vehicle, represented as a process case (`case:concept:name`).
_Avoid_: Run, journey, session

**Passage (Passagem)**:
A timestamped occurrence of a bus visiting or traversing the geofence/vicinity of a planned physical stop.
_Avoid_: Check-in, hit, waypoint event

**Shape (Traçado)**:
The ordered sequence of geographic coordinates defining the physical road geometry of a bus route.
_Avoid_: Path, polyline, trajectory geometry

**Stop Sequence (Sequência de Paradas)**:
The strictly ordered sequence of physical boarding points assigned to a directional route.
_Avoid_: Stop list, itinerary, stop schedule

**Operational Regime (Regime Operacional)**:
The operational schedule period and telemetry sampling cadence of the transit network:
- **Regime A (Out/2025)**: Standard collection (~120s interval), run from `2025-10-24 02:32:48` to `2025-10-29 12:29:23` (5 days, 9h 56m, ~5.08M GPS records across 127 hourly CSV files).
- **Regime B (Dez/2025)**: High-frequency collection (~20s interval), run from `2025-12-02 00:03:05` to `2025-12-08 23:27:09` (6 days, 23h 24m / ~7 days).
_Avoid_: Phase, schedule batch, version


### Telemetry Storage & Access

**Telemetry Repository (Repositório de Telemetria)**:
The unified data access gateway that provides static schedule data, real-time GPS streams, and processed event logs across storage adapters.
_Avoid_: Data fetcher, file scanner, folder reader

### Trajectory Reconstruction

**Trajectory Reconstruction (Reconstrução de Trajetória)**:
The pipeline that cleans raw telemetry, maps coordinates to physical shapes via HMM Viterbi projection, and estimates stop arrival times with monotonic PCHIP splines.
_Avoid_: Geofencing, map-matching script, data processor

**Map-Matching**:
The algorithmic projection of noisy GPS coordinates onto the discrete sequential nodes of the physical route shape.
_Avoid_: Snap-to-road, coordinate alignment

### Process Mining & Analytics

**Trace Fitness**:
The normalized metric (0.0 to 1.0) quantifying how strictly an observed trip adheres to the normative planned route sequence.
_Avoid_: Conformance score, compliance rate

**Deviation (Desvio)**:
An operational departure from the planned schedule or route, specifically skipped stops or unvisited sequence segments.
_Avoid_: Error, fault, exception

**Performance DFG**:
A Directly-Follows Graph annotated with empirical transit durations between consecutive stops to expose bottlenecks.
_Avoid_: Flow chart, transition diagram

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

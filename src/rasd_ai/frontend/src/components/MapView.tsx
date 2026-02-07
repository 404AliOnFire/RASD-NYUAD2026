import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
// Note: leaflet.heat removed - using pure React circles for better production compatibility
import { NodeRecord, PriorityRecord, RouteSummary, RouteData, ClosureRecord } from "../types";

interface MapViewProps {
  nodes: NodeRecord[];
  priorities: PriorityRecord[];
  routes: RouteData[];
  toggles: {
    pits: boolean;
    routes: boolean;
    closures: boolean;
    heatmap: boolean;
  };
  onSelectPit: (pit: PriorityRecord, visualOverride?: { level_pct: number; tier: string; priority: number; tto_hours: number }) => void;
  onSelectTruck: (summary: RouteSummary) => void;
  summaries: RouteSummary[];
  speed: number;
  focusTruckId: string | null;
  closures: ClosureRecord[];
  depot?: { id: string; lat: number; lon: number };
  onServicedCountChange?: (count: number) => void;
}

// Visual state for pit being serviced (all visual-only updates)
interface ServicedPitState {
  pitId: number;
  truckId: string;
  originalLevel: number;
  currentLevel: number;        // Current animated level
  phase: "draining" | "transitioning" | "done";
  colorPhase: "red" | "yellow" | "green";
  // Updated visual data after service
  newTier: "HIGH" | "MEDIUM" | "LOW";
  newPriority: number;
  newTtoHours: number;
}

// Truck animation state
interface TruckState {
  truckId: string;
  currentStopIndex: number;  // Which stop we're heading to (index in route.stops)
  progress: number;          // 0-1 progress between current stop and next
  isPaused: boolean;
  isFinished: boolean;       // Completed all stops, back at depot
  startDelay: number;        // Delay before this truck starts (ms)
  hasStarted: boolean;
}

// Truck icons
const truckIcon = L.divIcon({
  className: "",
  html: `<div style="filter: drop-shadow(0 0 6px #00f0ff);">
    <svg width='32' height='20' viewBox='0 0 56 36' xmlns='http://www.w3.org/2000/svg'>
      <rect x='2' y='10' width='34' height='16' rx='3' fill='#00f0ff'/>
      <rect x='36' y='14' width='14' height='12' rx='2' fill='#0b1020' stroke='#00f0ff' stroke-width='2'/>
      <circle cx='14' cy='28' r='5' fill='#0b1020' stroke='#00f0ff' stroke-width='2'/>
      <circle cx='36' cy='28' r='5' fill='#0b1020' stroke='#00f0ff' stroke-width='2'/>
    </svg>
  </div>`,
  iconSize: [32, 20],
  iconAnchor: [16, 10]
});

const truckStoppedIcon = L.divIcon({
  className: "",
  html: `<div style="filter: drop-shadow(0 0 10px #22c55e); animation: pulse 1s ease-in-out infinite;">
    <svg width='32' height='20' viewBox='0 0 56 36' xmlns='http://www.w3.org/2000/svg'>
      <rect x='2' y='10' width='34' height='16' rx='3' fill='#22c55e'/>
      <rect x='36' y='14' width='14' height='12' rx='2' fill='#0b1020' stroke='#22c55e' stroke-width='2'/>
      <circle cx='14' cy='28' r='5' fill='#0b1020' stroke='#22c55e' stroke-width='2'/>
      <circle cx='36' cy='28' r='5' fill='#0b1020' stroke='#22c55e' stroke-width='2'/>
    </svg>
  </div>`,
  iconSize: [32, 20],
  iconAnchor: [16, 10]
});

const depotIcon = L.divIcon({
  className: "",
  html: `<div style="filter: drop-shadow(0 0 8px #a855f7); background: #a855f7; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; font-weight: bold;">D</div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const routeColors = ["#00f0ff", "#22c55e", "#facc15", "#ff4fd8", "#a855f7", "#38bdf8"];

function tierColor(tier: string) {
  if (tier === "HIGH") return "#ff3b3b";
  if (tier === "MEDIUM") return "#facc15";
  return "#22c55e";
}

// Pure React heatmap implementation - works in production without leaflet.heat plugin
function HeatLayer({ points }: { points: Array<[number, number, number]> }) {
  if (!points.length) {
    return null;
  }

  // Render colored circles with gradient effect based on priority weight
  return (
    <>
      {points.map(([lat, lon, weight], idx) => {
        // Color gradient: green (low) -> yellow (medium) -> red (high)
        let color: string;
        let glowColor: string;
        if (weight > 0.7) {
          color = '#ff3b3b';
          glowColor = 'rgba(255, 59, 59, 0.4)';
        } else if (weight > 0.4) {
          color = '#facc15';
          glowColor = 'rgba(250, 204, 21, 0.4)';
        } else {
          color = '#22c55e';
          glowColor = 'rgba(34, 197, 94, 0.4)';
        }

        // Outer glow circle
        const outerRadius = 20 + weight * 35;
        // Inner solid circle
        const innerRadius = 8 + weight * 12;

        return (
          <React.Fragment key={`heat-${idx}`}>
            {/* Outer glow effect */}
            <CircleMarker
              center={[lat, lon]}
              radius={outerRadius}
              pathOptions={{
                stroke: false,
                fillColor: glowColor,
                fillOpacity: 0.25 + weight * 0.2,
              }}
            />
            {/* Middle glow */}
            <CircleMarker
              center={[lat, lon]}
              radius={outerRadius * 0.6}
              pathOptions={{
                stroke: false,
                fillColor: color,
                fillOpacity: 0.3 + weight * 0.15,
              }}
            />
            {/* Inner core */}
            <CircleMarker
              center={[lat, lon]}
              radius={innerRadius}
              pathOptions={{
                stroke: false,
                fillColor: color,
                fillOpacity: 0.5 + weight * 0.3,
              }}
            />
          </React.Fragment>
        );
      })}
    </>
  );
}

// Interpolate position between two coordinates
function interpolatePosition(
  from: { lat: number; lon: number },
  to: { lat: number; lon: number },
  t: number
) {
  return {
    lat: from.lat + (to.lat - from.lat) * t,
    lon: from.lon + (to.lon - from.lon) * t
  };
}

export default function MapView({
  nodes,
  priorities,
  routes,
  toggles,
  onSelectPit,
  onSelectTruck,
  summaries,
  speed,
  focusTruckId,
  closures,
  depot,
  onServicedCountChange
}: MapViewProps) {
  // Truck states - each truck has its own animation state
  const [truckStates, setTruckStates] = useState<Map<string, TruckState>>(new Map());
  const [servicedPits, setServicedPits] = useState<Map<number, ServicedPitState>>(new Map());
  const [drainAnimations, setDrainAnimations] = useState<Map<number, number>>(new Map());
  const [hiddenRoutes, setHiddenRoutes] = useState<Set<string>>(new Set());
  const [animationStartTime, setAnimationStartTime] = useState<number>(Date.now());

  const rafRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number | null>(null);

  // Build coordinate map from nodes
  const coordMap = useMemo(() => {
    const map = new Map<string | number, { lat: number; lon: number }>();
    nodes.forEach((n) => map.set(n.node_id, { lat: n.lat, lon: n.lon }));
    if (depot) map.set("depot", { lat: depot.lat, lon: depot.lon });
    return map;
  }, [nodes, depot]);

  // Priority map
  const priorityMap = useMemo(() => {
    const map = new Map<number, PriorityRecord>();
    priorities.forEach((p) => map.set(p.tank_id, p));
    return map;
  }, [priorities]);

  // Filter routes
  const filteredRoutes = useMemo(() => {
    if (!focusTruckId) return routes;
    return routes.filter((r) => r.truck_id === focusTruckId);
  }, [routes, focusTruckId]);

  // Pits
  const pits = useMemo(() => nodes.filter((n) => n.node_id !== "depot"), [nodes]);

  // Heatmap points
  const heatPoints = useMemo(() => {
    const maxPriority = Math.max(...priorities.map((p) => p.priority || 0), 1);
    return priorities
      .map((p) => {
        const coord = coordMap.get(p.tank_id);
        if (!coord) return null;
        const weight = Math.min(p.priority / maxPriority, 1);
        return [coord.lat, coord.lon, weight] as [number, number, number];
      })
      .filter(Boolean) as Array<[number, number, number]>;
  }, [priorities, coordMap]);

  // Report serviced pits count to parent
  useEffect(() => {
    const doneCount = Array.from(servicedPits.values()).filter(s => s.phase === "done").length;
    if (onServicedCountChange) {
      onServicedCountChange(doneCount);
    }
  }, [servicedPits, onServicedCountChange]);

  // Initialize truck states when routes change
  useEffect(() => {
    const newStates = new Map<string, TruckState>();
    filteredRoutes.forEach((route, idx) => {
      if (route.stops.length < 2) return;
      newStates.set(route.truck_id, {
        truckId: route.truck_id,
        currentStopIndex: 0,
        progress: 0,
        isPaused: false,
        isFinished: false,
        startDelay: idx * 3000, // Each truck starts 3 seconds after the previous
        hasStarted: false
      });
    });
    setTruckStates(newStates);
    setServicedPits(new Map());
    setDrainAnimations(new Map());
    setHiddenRoutes(new Set());
    setAnimationStartTime(Date.now());
  }, [filteredRoutes]);

  // Get position for a truck based on its state
  const getTruckPosition = useCallback((truckId: string) => {
    const state = truckStates.get(truckId);
    const route = filteredRoutes.find((r) => r.truck_id === truckId);
    if (!state || !route || route.stops.length < 2) return null;

    if (!state.hasStarted || state.isFinished) {
      // At depot
      const depotCoord = coordMap.get("depot");
      return depotCoord || { lat: 31.53, lon: 35.095 };
    }

    const fromStopId = route.stops[state.currentStopIndex];
    const toStopId = route.stops[state.currentStopIndex + 1];

    if (toStopId === undefined) {
      // At last stop
      const coord = coordMap.get(fromStopId);
      return coord || null;
    }

    const fromCoord = coordMap.get(fromStopId);
    const toCoord = coordMap.get(toStopId);

    if (!fromCoord || !toCoord) return fromCoord || toCoord || null;

    return interpolatePosition(fromCoord, toCoord, state.progress);
  }, [truckStates, filteredRoutes, coordMap]);

  // Start drain animation
  const startDrainAnimation = useCallback((pitId: number, truckId: string, originalLevel: number, originalPriority: number, originalTto: number) => {
    console.log(`[RASD] 🚛 بدء تفريغ الحفرة #${pitId}`);

    // Calculate new values after service (visual only)
    const newTier = "LOW" as const;
    const newPriority = Math.max(0.05, originalPriority * 0.1);
    const newTtoHours = Math.max(168, originalTto * 5);

    setServicedPits((prev) => {
      const newMap = new Map(prev);
      newMap.set(pitId, {
        pitId,
        truckId,
        originalLevel,
        currentLevel: originalLevel,
        phase: "draining",
        colorPhase: "red",
        newTier,
        newPriority,
        newTtoHours
      });
      return newMap;
    });

    const targetLevel = 0;
    const duration = 3500;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const animProgress = Math.min(elapsed / duration, 1);
      const eased = animProgress < 0.5
        ? 2 * animProgress * animProgress
        : 1 - Math.pow(-2 * animProgress + 2, 2) / 2;

      const currentLevel = Math.round(originalLevel - (originalLevel - targetLevel) * eased);

      // Update current level in state
      setServicedPits((prev) => {
        const newMap = new Map(prev);
        const state = newMap.get(pitId);
        if (state) newMap.set(pitId, { ...state, currentLevel });
        return newMap;
      });

      setDrainAnimations((prev) => new Map(prev).set(pitId, currentLevel));

      if (animProgress < 1) {
        requestAnimationFrame(animate);
      } else {
        // Done draining
        setServicedPits((prev) => {
          const newMap = new Map(prev);
          const state = newMap.get(pitId);
          if (state) newMap.set(pitId, { ...state, phase: "transitioning", colorPhase: "yellow", currentLevel: 0 });
          return newMap;
        });

        setTimeout(() => {
          setServicedPits((prev) => {
            const newMap = new Map(prev);
            const state = newMap.get(pitId);
            if (state) newMap.set(pitId, { ...state, colorPhase: "green", phase: "done" });
            return newMap;
          });

          // Resume truck
          setTruckStates((prev) => {
            const newMap = new Map(prev);
            const state = newMap.get(truckId);
            if (state) {
              newMap.set(truckId, { ...state, isPaused: false });
            }
            return newMap;
          });
        }, 800);
      }
    };

    requestAnimationFrame(animate);
  }, []);

  // Check if truck arrived at a HIGH pit
  const checkArrivalAtPit = useCallback((truckId: string, stopId: string | number) => {
    if (stopId === "depot") return;

    const priority = priorityMap.get(stopId as number);
    if (!priority || priority.tier !== "HIGH") return;

    // Check current servicedPits state
    setServicedPits((currentServiced) => {
      if (currentServiced.has(stopId as number)) return currentServiced;

      // Pause only this specific truck
      setTruckStates((prev) => {
        const newMap = new Map(prev);
        const state = newMap.get(truckId);
        if (state && !state.isPaused) {
          newMap.set(truckId, { ...state, isPaused: true });
        }
        return newMap;
      });

      // Start drain animation after delay
      setTimeout(() => {
        startDrainAnimation(
          stopId as number,
          truckId,
          priority.level_pct,
          priority.priority,
          priority.tto_hours
        );
      }, 300);

      return currentServiced;
    });
  }, [priorityMap, startDrainAnimation]);

  // Main animation loop
  useEffect(() => {
    const baseSpeed = 0.0008 * speed; // Progress per ms

    const loop = (time: number) => {
      if (!lastTimeRef.current) lastTimeRef.current = time;
      const delta = time - lastTimeRef.current;
      lastTimeRef.current = time;

      const elapsed = Date.now() - animationStartTime;

      setTruckStates((prev) => {
        const newMap = new Map(prev);
        let needsUpdate = false;

        prev.forEach((state, truckId) => {
          // Check if truck should start
          if (!state.hasStarted && elapsed >= state.startDelay) {
            newMap.set(truckId, { ...state, hasStarted: true });
            needsUpdate = true;
            return;
          }

          // Skip trucks that are paused, finished, or not started
          if (!state.hasStarted || state.isPaused || state.isFinished) return;

          const route = filteredRoutes.find((r) => r.truck_id === truckId);
          if (!route) return;

          let newProgress = state.progress + baseSpeed * delta;
          let newStopIndex = state.currentStopIndex;

          // Check if reached next stop
          if (newProgress >= 1) {
            newProgress = 0;
            newStopIndex++;

            // Check if finished all stops
            if (newStopIndex >= route.stops.length - 1) {
              // Truck finished - hide its route
              setHiddenRoutes((prevHidden) => new Set(prevHidden).add(truckId));
              newMap.set(truckId, { ...state, isFinished: true, currentStopIndex: newStopIndex });
              console.log(`[RASD] 🏁 الشاحنة ${truckId} أنهت مسارها`);
              needsUpdate = true;
              return;
            }

            // Check if arrived at a HIGH pit - use setTimeout to avoid state conflicts
            const arrivedAtStop = route.stops[newStopIndex];
            if (arrivedAtStop !== "depot") {
              setTimeout(() => checkArrivalAtPit(truckId, arrivedAtStop), 10);
            }
          }

          newMap.set(truckId, { ...state, progress: newProgress, currentStopIndex: newStopIndex });
          needsUpdate = true;
        });

        return needsUpdate ? newMap : prev;
      });

      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      lastTimeRef.current = null;
    };
  }, [speed, filteredRoutes, animationStartTime, checkArrivalAtPit]);

  const depotCoord = depot || { lat: 31.53, lon: 35.095 };

  // Get visual color for pit
  const getPitVisualColor = (pitId: number, originalTier: string) => {
    const state = servicedPits.get(pitId);
    if (state) {
      switch (state.colorPhase) {
        case "red": return "#ff3b3b";
        case "yellow": return "#facc15";
        case "green": return "#22c55e";
      }
    }
    return tierColor(originalTier);
  };

  // Get visual level for pit
  const getPitVisualLevel = (pitId: number, originalLevel: number) => {
    return drainAnimations.get(pitId) ?? originalLevel;
  };

  return (
    <div className="panel h-full min-h-[600px]">
      <MapContainer center={[31.53, 35.095]} zoom={12} className="h-full w-full rounded-xl" style={{ minHeight: "600px" }}>
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Heatmap */}
        {toggles.heatmap && heatPoints.length > 0 && <HeatLayer points={heatPoints} />}

        {/* Road Closures (data only) */}
        {toggles.closures && closures?.length > 0 && closures
          .map((c) => {
            const from = coordMap.get(c.from);
            const to = coordMap.get(c.to);
            if (!from || !to) return null;
            return {
              key: `${c.from}-${c.to}`,
              positions: [[from.lat, from.lon], [to.lat, to.lon]] as [number, number][]
            };
          })
          .filter(Boolean)
          .map((line) => (
            <Polyline
              key={line!.key}
              positions={line!.positions}
              pathOptions={{ color: "#ff3b3b", weight: 4, opacity: 0.7, dashArray: "8, 8" }}
            />
          ))}

        {/* Route Polylines - hide finished routes */}
        {toggles.routes && filteredRoutes.map((route, idx) => {
          if (route.polyline.length < 2) return null;
          if (hiddenRoutes.has(route.truck_id)) return null;

          const isFocused = focusTruckId === route.truck_id;
          const positions = route.polyline.map(([lat, lon]) => [lat, lon] as [number, number]);

          return (
            <Polyline
              key={route.truck_id}
              positions={positions}
              pathOptions={{
                color: routeColors[idx % routeColors.length],
                weight: isFocused ? 6 : 4,
                opacity: isFocused || !focusTruckId ? 0.9 : 0.3
              }}
            >
              <Popup>{route.truck_id.replace("_", " ").toUpperCase()}</Popup>
            </Polyline>
          );
        })}

        {/* Tank Markers */}
        {toggles.pits && pits.map((pit) => {
          const priority = priorities.find((p) => p.tank_id === pit.node_id);
          const originalTier = priority?.tier ?? "LOW";
          const originalLevel = priority?.level_pct ?? 0;
          const servicedState = servicedPits.get(pit.node_id as number);

          const visualColor = getPitVisualColor(pit.node_id as number, originalTier);
          const visualLevel = getPitVisualLevel(pit.node_id as number, originalLevel);
          const isBeingServiced = servicedState?.phase === "draining";
          const isDone = servicedState?.phase === "done";
          const radius = isBeingServiced ? 14 : isDone ? 9 : originalTier === "HIGH" ? 10 : 8;
          const weight = isBeingServiced ? 4 : originalTier === "HIGH" ? 3 : 2;
          const className = isBeingServiced ? "pit-servicing" : isDone ? "pit-done" : originalTier === "HIGH" ? "glow-high" : "";

          const handleClick = () => {
            if (!priority) return;
            if (servicedState && (servicedState.phase === "done" || servicedState.phase === "draining")) {
              onSelectPit(priority, {
                level_pct: servicedState.currentLevel,
                tier: servicedState.newTier,
                priority: servicedState.newPriority,
                tto_hours: servicedState.newTtoHours
              });
              return;
            }
            onSelectPit(priority);
          };

          return (
            <CircleMarker
              key={String(pit.node_id)}
              center={[pit.lat, pit.lon]}
              radius={radius}
              pathOptions={{
                color: visualColor,
                fillColor: visualColor,
                fillOpacity: isBeingServiced ? 1 : 0.85,
                weight,
                className
              }}
              eventHandlers={{ click: handleClick }}
            >
              <Popup>
                <div className="text-center">
                  <strong>خزان #{pit.node_id}</strong><br/>
                  المستوى: {visualLevel}%<br/>
                  {isBeingServiced && <span style={{color: '#22c55e'}}>جاري التفريغ...</span>}
                  {isDone && <span style={{color: '#22c55e'}}>✅ تم التفريغ</span>}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Floating Level Indicator */}
        {Array.from(servicedPits.entries()).map(([pitId, state]) => {
          if (state.phase !== "draining") return null;
          const coord = coordMap.get(pitId);
          if (!coord) return null;
          const level = drainAnimations.get(pitId) ?? state.originalLevel;
          const levelColor = level > 50 ? "#ff3b3b" : level > 30 ? "#facc15" : "#22c55e";

          return (
            <Marker
              key={`level-${pitId}`}
              position={[coord.lat + 0.003, coord.lon]}
              icon={L.divIcon({
                className: "",
                html: `<div style="
                  background: linear-gradient(135deg, #0b1020 0%, #1a1a2e 100%);
                  border: 2px solid ${levelColor};
                  border-radius: 8px;
                  padding: 6px 12px;
                  color: white;
                  font-weight: bold;
                  text-align: center;
                ">
                  <div style="font-size: 10px; opacity: 0.7;">جاري التفريغ</div>
                  <div style="font-size: 18px;">${level}%</div>
                  <div style="width:100%;height:4px;background:#333;border-radius:2px;margin-top:4px;overflow:hidden;">
                    <div style="width:${level}%;height:100%;background:${levelColor};"></div>
                  </div>
                </div>`,
                iconSize: [80, 60],
                iconAnchor: [40, 60]
              })}
            />
          );
        })}

        {/* Depot */}
        <Marker position={[depotCoord.lat, depotCoord.lon]} icon={depotIcon}>
          <Popup><strong>المركز</strong></Popup>
        </Marker>

        {/* Trucks */}
        {Array.from(truckStates.entries()).map(([truckId, state]) => {
          if (!state.hasStarted) return null;
          const pos = getTruckPosition(truckId);
          if (!pos) return null;

          return (
            <Marker
              key={truckId}
              position={[pos.lat, pos.lon]}
              icon={state.isPaused ? truckStoppedIcon : truckIcon}
              eventHandlers={{
                click: () => {
                  const summary = summaries.find((s) => s.truckId === truckId);
                  if (summary) onSelectTruck(summary);
                }
              }}
            >
              <Popup>
                <strong>{truckId.replace("_", " ").toUpperCase()}</strong>
                {state.isPaused && <div style={{color: '#22c55e'}}>جاري التفريغ...</div>}
                {state.isFinished && <div style={{color: '#a855f7'}}>أنهى المسار</div>}
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}


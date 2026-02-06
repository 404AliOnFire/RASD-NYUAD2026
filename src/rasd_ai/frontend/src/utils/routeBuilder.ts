import { NodeId, QuantumRoute } from "../types";
import { haversineKm } from "./geo";

export function buildNearestNeighborSequence(
  assigned: number[],
  coordMap: Map<NodeId, { lat: number; lon: number }>,
  start: NodeId = "depot"
) {
  const remaining = new Set<number>(assigned);
  const sequence: NodeId[] = [start];
  let current: NodeId = start;

  while (remaining.size > 0) {
    const cur = coordMap.get(current);
    if (!cur) break;
    let bestId: number | null = null;
    let bestDist = Number.POSITIVE_INFINITY;
    remaining.forEach((pid) => {
      const next = coordMap.get(pid);
      if (!next) return;
      const d = haversineKm(cur, next);
      if (d < bestDist) {
        bestDist = d;
        bestId = pid;
      }
    });
    if (bestId === null) break;
    sequence.push(bestId);
    remaining.delete(bestId);
    current = bestId;
  }

  sequence.push(start);
  return sequence;
}

export function buildSequenceFromAssignedPits(
  assignedPits: number[],
  coordMap: Map<NodeId, { lat: number; lon: number }>
): NodeId[] {
  const missing: Array<NodeId> = [];
  const depot = coordMap.get("depot") ? "depot" : null;

  assignedPits.forEach((pid) => {
    if (!coordMap.get(pid)) missing.push(pid);
  });
  if (!depot) missing.push("depot");

  if (missing.length > 0) {
    console.warn(`[RASD] Missing coordinates for node ids: ${missing.join(", ")}`);
  }

  const start: NodeId = depot ?? assignedPits[0] ?? "depot";
  return buildNearestNeighborSequence(assignedPits, coordMap, start);
}

export function buildQuantumSequences(
  quantumRoutes: Record<string, QuantumRoute>,
  coordMap: Map<NodeId, { lat: number; lon: number }>
) {
  const result: Record<string, NodeId[]> = {};
  Object.entries(quantumRoutes).forEach(([truckId, info]) => {
    if (!info.assigned_pits || info.assigned_pits.length === 0) return;
    result[truckId] = buildSequenceFromAssignedPits(info.assigned_pits, coordMap);
  });
  return result;
}

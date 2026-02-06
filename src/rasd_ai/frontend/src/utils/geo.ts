import { NodeId, NodeRecord } from "../types";

export function buildCoordMap(nodes: NodeRecord[]) {
  const map = new Map<NodeId, { lat: number; lon: number }>();
  nodes.forEach((n) => map.set(n.node_id, { lat: n.lat, lon: n.lon }));
  return map;
}

export function haversineKm(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const R = 6371;
  const p1 = (a.lat * Math.PI) / 180;
  const p2 = (b.lat * Math.PI) / 180;
  const dLat = p2 - p1;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export function routeDistanceKm(sequence: NodeId[], coordMap: Map<NodeId, { lat: number; lon: number }>) {
  let total = 0;
  for (let i = 0; i < sequence.length - 1; i += 1) {
    const a = coordMap.get(sequence[i]);
    const b = coordMap.get(sequence[i + 1]);
    if (!a || !b) continue;
    total += haversineKm(a, b);
  }
  return total;
}

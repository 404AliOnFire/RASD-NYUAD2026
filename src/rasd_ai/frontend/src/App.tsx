import { useEffect, useMemo, useState } from "react";
import Tabs from "./components/Tabs";
import MapView from "./components/MapView";
import ControlPanel from "./components/ControlPanel";
import DetailsPanel from "./components/DetailsPanel";
import TrucksTab from "./components/TrucksTab";
import TanksTab from "./components/TanksTab";
import AlertsTab from "./components/AlertsTab";
import InfoTab from "./components/InfoTab";
import StatsTab from "./components/StatsTab";
import { loadAllData } from "./utils/dataLoader";
import { PriorityRecord, RouteSummary, RouteData } from "./types";
import { useLanguage } from "./useLanguage";

export default function App() {
  const { t, toggleLang, fontClass, dir, lang } = useLanguage();
  const [activeTab, setActiveTab] = useState("home");
  const [toastMessages, setToastMessages] = useState<string[]>([]);

  const [data, setData] = useState<Awaited<ReturnType<typeof loadAllData>> | null>(null);
  const [selectedPit, setSelectedPit] = useState<PriorityRecord | null>(null);
  const [selectedPitVisualOverride, setSelectedPitVisualOverride] = useState<{
    level_pct: number;
    tier: string;
    priority: number;
    tto_hours: number;
  } | null>(null);
  const [selectedTruck, setSelectedTruck] = useState<RouteSummary | null>(null);
  const [toggles, setToggles] = useState({ pits: true, routes: true, closures: false, heatmap: false });
  const [speed, setSpeed] = useState(0.5);
  const [focusTruckId, setFocusTruckId] = useState<string | null>(null);
  const [servicedPitsCount, setServicedPitsCount] = useState(0);

  // Handle pit selection with optional visual override
  const handleSelectPit = (pit: PriorityRecord, visualOverride?: { level_pct: number; tier: string; priority: number; tto_hours: number }) => {
    setSelectedPit(pit);
    setSelectedPitVisualOverride(visualOverride || null);
  };

  // Tab configuration
  const tabConfig = useMemo(
    () => [
      { key: "home", label: t("tabHome") },
      { key: "trucks", label: t("tabTrucks") },
      { key: "tanks", label: t("tabTanks") },
      { key: "stats", label: t("tabStats") },
      { key: "alerts", label: t("tabAlerts") },
      { key: "info", label: t("tabInfo") },
    ],
    [t, lang]
  );

  // Auto-load data on startup
  useEffect(() => {
    loadAllData().then((loaded) => {
      setData(loaded);
      setToastMessages(loaded.toastMessages);
      console.log("[RASD] === البيانات جاهزة ===");
    });
  }, []);

  // Get quantum routes (optimized plan)
  const quantumRoutes = useMemo<RouteData[]>(() => {
    if (!data?.routesForFrontend?.routes?.quantum) {
      console.warn("[RASD] لا توجد مسارات محسّنة");
      return [];
    }
    const routes = data.routesForFrontend.routes.quantum.filter(
      (r) => r.stops.length > 2 && r.polyline.length > 1
    );
    console.log(`[RASD] تم تحميل ${routes.length} مسارات محسّنة`);
    return routes;
  }, [data]);

  // Build route summaries for display
  const routeSummaries = useMemo<RouteSummary[]>(() => {
    return quantumRoutes.map((route) => {
      // Calculate distance from polyline
      let distance_km = 0;
      for (let i = 0; i < route.polyline.length - 1; i++) {
        const [lat1, lon1] = route.polyline[i];
        const [lat2, lon2] = route.polyline[i + 1];
        const dx = (lat2 - lat1) * 111.32;
        const dy = (lon2 - lon1) * 111.32 * Math.cos((lat1 * Math.PI) / 180);
        distance_km += Math.sqrt(dx * dx + dy * dy);
      }

      const pitIds = route.stops.filter((s) => s !== "depot") as number[];
      const stopsCount = pitIds.length;
      const fuel_l = distance_km * 0.35;
      const co2_kg = fuel_l * 2.68;
      const fuel_cost_usd = fuel_l * 1.8;
      const eta_min = (distance_km / 25) * 60 + 10 * stopsCount;

      return {
        truckId: route.truck_id,
        stops: route.stops,
        polyline: route.polyline,
        pitIds,
        stopsCount,
        distance_km,
        fuel_l,
        co2_kg,
        fuel_cost_usd,
        eta_min,
      };
    });
  }, [quantumRoutes]);

  // Metrics
  const metrics = useMemo(() => {
    if (data?.quantumMetrics) return data.quantumMetrics;
    // Compute from routes if not available
    return {
      total_distance_km: routeSummaries.reduce((sum, r) => sum + r.distance_km, 0),
      served_total: routeSummaries.reduce((sum, r) => sum + r.stopsCount, 0),
      high_served: data?.priorities.filter((p) => p.tier === "HIGH").length ?? 0,
      high_total: data?.priorities.filter((p) => p.tier === "HIGH").length ?? 0,
      medium_served: data?.priorities.filter((p) => p.tier === "MEDIUM").length ?? 0,
      medium_total: data?.priorities.filter((p) => p.tier === "MEDIUM").length ?? 0,
      low_served: 0,
      low_total: data?.priorities.filter((p) => p.tier === "LOW").length ?? 0,
      fuel_l_est: routeSummaries.reduce((sum, r) => sum + r.fuel_l, 0),
      co2_kg_est: routeSummaries.reduce((sum, r) => sum + r.co2_kg, 0),
    };
  }, [data, routeSummaries]);

  // Loading state
  if (!data) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${fontClass}`} dir={dir}>
        <div className="panel p-8 text-center">
          <img src="/logo/RASD.png" alt="RASD" className="h-20 mx-auto mb-4" />
          <div className="text-xl font-bold text-neon-cyan">{t("loading")}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${fontClass}`} dir={dir}>
      {/* Header */}
      <header className="bg-panel border-b border-grid px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center gap-4">
            <img src="/logo/RASD.png" alt="RASD" className="h-14 md:h-16 w-auto" />
            <div>
              <h1 className="text-2xl font-bold text-neon-cyan">{t("appTitle")}</h1>
              <p className="text-sm text-slate-400">{t("appSubtitle")}</p>
            </div>
          </div>

          {/* Language Toggle */}
          <button
            type="button"
            className="panel-soft px-4 py-2 text-sm font-medium hover:border-neon-cyan transition"
            onClick={toggleLang}
          >
            {lang === "ar" ? "EN" : "عربي"}
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div className="px-4 py-3 border-b border-grid bg-panel/50">
        <Tabs active={activeTab} setActive={setActiveTab} tabs={tabConfig} />
      </div>

      {/* Main Content */}
      <main className="p-4">
        {/* Home Tab - Map View */}
        {activeTab === "home" && (
          <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr_300px] gap-4">
            <ControlPanel
              metrics={metrics}
              toggles={toggles}
              setToggles={setToggles}
              speed={speed}
              setSpeed={setSpeed}
              priorities={data.priorities}
              summaries={routeSummaries}
              focusTruckId={focusTruckId}
              setFocusTruckId={setFocusTruckId}
              servicedPitsCount={servicedPitsCount}
              t={t}
            />

            <MapView
              nodes={data.nodes}
              priorities={data.priorities}
              routes={quantumRoutes}
              toggles={toggles}
              onSelectPit={handleSelectPit}
              onSelectTruck={(summary) => setSelectedTruck(summary)}
              summaries={routeSummaries}
              speed={speed}
              focusTruckId={focusTruckId}
              closures={data.closures}
              depot={data.routesForFrontend?.depot}
              onServicedCountChange={setServicedPitsCount}
            />

            <DetailsPanel
              selectedPit={selectedPit}
              selectedTruck={selectedTruck}
              visualOverride={selectedPitVisualOverride}
              t={t}
            />
          </div>
        )}

        {/* Trucks Tab */}
        {activeTab === "trucks" && (
          <TrucksTab
            routes={quantumRoutes}
            summaries={routeSummaries}
            priorities={data.priorities}
            t={t}
          />
        )}

        {/* Tanks Tab */}
        {activeTab === "tanks" && (
          <TanksTab
            priorities={data.priorities}
            nodes={data.nodes}
            onSelectTank={(tank) => {
              setSelectedPit(tank);
              setActiveTab("home");
            }}
            t={t}
          />
        )}

        {/* Stats Tab */}
        {activeTab === "stats" && (
          <StatsTab
            priorities={data.priorities}
            summaries={routeSummaries}
            metrics={metrics}
            t={t}
          />
        )}

        {/* Alerts Tab */}
        {activeTab === "alerts" && <AlertsTab priorities={data.priorities} t={t} />}

        {/* Info Tab */}
        {activeTab === "info" && <InfoTab t={t} />}
      </main>

      {/* Toast Messages */}
      {toastMessages.length > 0 && (
        <div className="fixed bottom-4 left-4 space-y-2 max-w-sm z-50">
          {toastMessages.map((msg, idx) => (
            <div key={`${msg}-${idx}`} className="panel-soft px-4 py-2 text-sm text-slate-200">
              ⚠️ {msg}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

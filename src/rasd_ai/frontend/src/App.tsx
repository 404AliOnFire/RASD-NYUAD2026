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
      {/* Header - Mobile Responsive */}
      <header className="bg-panel border-b border-grid px-3 md:px-4 py-2 md:py-3 mobile-header">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center gap-2 md:gap-4">
            <img src="/logo/RASD.png" alt="RASD" className="h-10 md:h-14 lg:h-16 w-auto" />
            <div className="min-w-0">
              <h1 className="text-lg md:text-2xl font-bold text-neon-cyan truncate">{t("appTitle")}</h1>
              <p className="text-xs md:text-sm text-slate-400 hidden sm:block">{t("appSubtitle")}</p>
            </div>
          </div>

          {/* Language Toggle */}
          <button
            type="button"
            className="panel-soft px-3 md:px-4 py-1.5 md:py-2 text-xs md:text-sm font-medium hover:border-neon-cyan transition flex-shrink-0"
            onClick={toggleLang}
          >
            {lang === "ar" ? "EN" : "عربي"}
          </button>
        </div>
      </header>

      {/* Tabs - Scrollable on mobile */}
      <div className="px-2 md:px-4 py-2 md:py-3 border-b border-grid bg-panel/50 mobile-tabs">
        <Tabs active={activeTab} setActive={setActiveTab} tabs={tabConfig} />
      </div>

      {/* Main Content */}
      <main className="p-2 md:p-4">
        {/* Home Tab - Map View */}
        {activeTab === "home" && (
          <>
            {/* Mobile: Stack vertically, Desktop: 3-column grid */}
            <div className="hidden xl:grid xl:grid-cols-[320px_1fr_300px] gap-4">
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

            {/* Mobile Layout */}
            <div className="xl:hidden space-y-3">
              {/* Quick Stats - 2x2 grid on mobile */}
              <div className="grid grid-cols-2 gap-2">
                <div className="panel p-3 text-center mobile-stat-card">
                  <div className="text-2xl md:text-3xl font-bold text-neon-cyan">{routeSummaries.length}</div>
                  <div className="text-xs text-slate-400">{t("activeTrucks")}</div>
                </div>
                <div className="panel p-3 text-center mobile-stat-card">
                  <div className="text-2xl md:text-3xl font-bold text-red-400">
                    {data.priorities.filter((p) => p.tier === "HIGH").length}
                  </div>
                  <div className="text-xs text-slate-400">{t("criticalAlerts")}</div>
                </div>
                <div className="panel p-3 text-center mobile-stat-card">
                  <div className="text-2xl md:text-3xl font-bold text-green-400">{servicedPitsCount}</div>
                  <div className="text-xs text-slate-400">{t("servicedTanks")}</div>
                </div>
                <div className="panel p-3 text-center mobile-stat-card">
                  <div className="text-2xl md:text-3xl font-bold text-purple-400">{data.priorities.length}</div>
                  <div className="text-xs text-slate-400">{t("tanksMonitored")}</div>
                </div>
              </div>

              {/* Map Controls - Horizontal scroll on mobile */}
              <div className="panel p-2 overflow-x-auto hide-scrollbar">
                <div className="flex gap-2 min-w-max">
                  <label className="toggle-pill cursor-pointer">
                    <input
                      type="checkbox"
                      checked={toggles.pits}
                      onChange={(e) => setToggles({ ...toggles, pits: e.target.checked })}
                      className="sr-only"
                    />
                    <span className={`w-3 h-3 rounded-full ${toggles.pits ? 'bg-neon-cyan' : 'bg-gray-500'}`} />
                    <span className="text-xs">{t("showTanks")}</span>
                  </label>
                  <label className="toggle-pill cursor-pointer">
                    <input
                      type="checkbox"
                      checked={toggles.routes}
                      onChange={(e) => setToggles({ ...toggles, routes: e.target.checked })}
                      className="sr-only"
                    />
                    <span className={`w-3 h-3 rounded-full ${toggles.routes ? 'bg-neon-cyan' : 'bg-gray-500'}`} />
                    <span className="text-xs">{t("showRoutes")}</span>
                  </label>
                  <label className="toggle-pill cursor-pointer">
                    <input
                      type="checkbox"
                      checked={toggles.heatmap}
                      onChange={(e) => setToggles({ ...toggles, heatmap: e.target.checked })}
                      className="sr-only"
                    />
                    <span className={`w-3 h-3 rounded-full ${toggles.heatmap ? 'bg-neon-cyan' : 'bg-gray-500'}`} />
                    <span className="text-xs">{t("showHeatmap")}</span>
                  </label>
                </div>
              </div>

              {/* Map - Larger on mobile */}
              <div className="map-mobile rounded-xl overflow-hidden" style={{ minHeight: '50vh' }}>
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
              </div>

              {/* Speed Slider */}
              <div className="panel p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400">{t("animationSpeed")}</span>
                  <span className="text-xs text-neon-cyan">{speed.toFixed(1)}x</span>
                </div>
                <input
                  type="range"
                  min="0.25"
                  max="2"
                  step="0.25"
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="w-full h-2 bg-panel-soft rounded-lg appearance-none cursor-pointer"
                />
              </div>

              {/* Details Drawer - Shows when something is selected */}
              {(selectedPit || selectedTruck) && (
                <div className="panel p-3">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold">{t("details")}</h3>
                    <button
                      onClick={() => { setSelectedPit(null); setSelectedTruck(null); }}
                      className="text-slate-400 hover:text-white text-lg"
                    >
                      ✕
                    </button>
                  </div>
                  <DetailsPanel
                    selectedPit={selectedPit}
                    selectedTruck={selectedTruck}
                    visualOverride={selectedPitVisualOverride}
                    t={t}
                  />
                </div>
              )}
            </div>
          </>
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

      {/* Toast Messages - Mobile friendly positioning */}
      {toastMessages.length > 0 && (
        <div className="fixed bottom-4 left-2 right-2 md:left-4 md:right-auto space-y-2 max-w-sm z-50">
          {toastMessages.map((msg, idx) => (
            <div key={`${msg}-${idx}`} className="panel-soft px-3 py-2 text-xs md:text-sm text-slate-200">
              ⚠️ {msg}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

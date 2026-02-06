export type Language = "ar" | "en";

type TranslationDict = Record<string, { ar: string; en: string }>;

export const translations: TranslationDict = {
  // Header
  appTitle: { ar: "نظام RASD", en: "RASD System" },
  appSubtitle: { ar: "إدارة جمع النفايات الذكية", en: "Smart Waste Collection Management" },

  // Tabs
  tabHome: { ar: "الرئيسية", en: "Home" },
  tabRoutes: { ar: "المسارات", en: "Routes" },
  tabTrucks: { ar: "الشاحنات", en: "Trucks" },
  tabTanks: { ar: "الخزانات", en: "Tanks" },
  tabAlerts: { ar: "التنبيهات", en: "Alerts" },
  tabInfo: { ar: "معلومات", en: "Info" },

  // KPI Summary
  kpiSummary: { ar: "ملخص الأداء", en: "Performance Summary" },
  optimizedPlan: { ar: "خطة الجمع المحسّنة", en: "Optimized Collection Plan" },

  // Status cards
  activeTrucks: { ar: "الشاحنات النشطة", en: "Active Trucks" },
  tanksMonitored: { ar: "الخزانات المراقبة", en: "Tanks Monitored" },
  criticalAlerts: { ar: "تنبيهات حرجة", en: "Critical Alerts" },
  totalAlerts: { ar: "إجمالي التنبيهات", en: "Total Alerts" },
  servicedTanks: { ar: "تم تفريغها", en: "Tanks Serviced" },

  // Map controls
  mapLayers: { ar: "تحكم الخريطة", en: "Map Controls" },
  showTanks: { ar: "إظهار الخزانات", en: "Show Tanks" },
  showRoutes: { ar: "إظهار المسارات", en: "Show Routes" },
  showClosures: { ar: "إظهار إغلاقات الطرق", en: "Show Road Closures" },
  showHeatmap: { ar: "خريطة الأولوية", en: "Priority Heatmap" },
  animationSpeed: { ar: "سرعة الحركة", en: "Animation Speed" },

  // Metrics
  totalDistance: { ar: "المسافة الإجمالية", en: "Total Distance" },
  servedTotal: { ar: "الخزانات المخدومة", en: "Tanks Served" },
  highServed: { ar: "أولوية عالية", en: "High Priority" },
  mediumServed: { ar: "أولوية متوسطة", en: "Medium Priority" },
  lowServed: { ar: "أولوية منخفضة", en: "Low Priority" },
  fuelEstimate: { ar: "تقدير الوقود", en: "Fuel Estimate" },
  co2Estimate: { ar: "انبعاثات CO₂", en: "CO₂ Emissions" },

  // Tanks
  tanksList: { ar: "قائمة الخزانات", en: "Tanks List" },
  tankId: { ar: "رقم الخزان", en: "Tank ID" },
  fillLevel: { ar: "نسبة الامتلاء", en: "Fill Level" },
  timeToOverflow: { ar: "الوقت للفيضان", en: "Time to Overflow" },
  priority: { ar: "الأولوية", en: "Priority" },
  tier: { ar: "المستوى", en: "Tier" },

  // Tier labels
  tierHigh: { ar: "عالي", en: "HIGH" },
  tierMedium: { ar: "متوسط", en: "MEDIUM" },
  tierLow: { ar: "منخفض", en: "LOW" },

  // Trucks
  trucksList: { ar: "قائمة الشاحنات", en: "Trucks List" },
  truckRoute: { ar: "مسار الشاحنة", en: "Truck Route" },
  routeSteps: { ar: "خطوات المسار", en: "Route Steps" },
  startFromDepot: { ar: "ابدأ من المركز", en: "Start from Depot" },
  returnToDepot: { ar: "عودة للمركز", en: "Return to Depot" },
  tank: { ar: "خزان", en: "Tank" },
  stops: { ar: "محطات", en: "Stops" },
  distance: { ar: "المسافة", en: "Distance" },
  fuel: { ar: "الوقود", en: "Fuel" },
  co2: { ar: "CO₂", en: "CO₂" },
  cost: { ar: "التكلفة", en: "Cost" },
  eta: { ar: "الوقت المقدر", en: "ETA" },

  // Truck instructions
  operatorInstructions: { ar: "تعليمات المشغل", en: "Operator Instructions" },
  startImmediately: { ar: "ابدأ فوراً، أولوية للخزانات الحمراء", en: "Start immediately, prioritize red tanks" },
  afterTruck: { ar: "بعد انتهاء الشاحنة السابقة", en: "After previous truck finishes" },
  highPriorityCount: { ar: "خزانات عالية الأولوية", en: "High priority tanks" },

  // Details panel
  details: { ar: "التفاصيل", en: "Details" },
  selectHint: { ar: "انقر على خزان أو شاحنة لعرض التفاصيل", en: "Click a tank or truck to view details" },
  sensorReadings: { ar: "قراءات المستشعرات", en: "Sensor Readings" },
  riskBreakdown: { ar: "تحليل المخاطر", en: "Risk Breakdown" },
  gasLevel: { ar: "مستوى الغاز", en: "Gas Level" },
  temperature: { ar: "درجة الحرارة", en: "Temperature" },
  humidity: { ar: "الرطوبة", en: "Humidity" },

  // Alerts
  alertsTitle: { ar: "التنبيهات الحرجة", en: "Critical Alerts" },
  noAlerts: { ar: "لا توجد تنبيهات حرجة حالياً", en: "No critical alerts at this time" },
  urgentAlerts: { ar: "تنبيهات عاجلة (أقل من 12 ساعة)", en: "Urgent Alerts (< 12h)" },
  warningAlerts: { ar: "تحذيرات (12-24 ساعة)", en: "Warnings (12-24h)" },

  // Filters
  filterAll: { ar: "الكل", en: "All" },
  filterHigh: { ar: "عالي", en: "High" },
  filterMedium: { ar: "متوسط", en: "Medium" },
  filterLow: { ar: "منخفض", en: "Low" },
  search: { ar: "بحث...", en: "Search..." },
  sortBy: { ar: "ترتيب حسب", en: "Sort by" },

  // Info tab
  infoTitle: { ar: "معلومات النظام", en: "System Information" },
  infoDesc: { ar: "نظام RASD لإدارة جمع النفايات الذكية في الخليل", en: "RASD smart waste collection management system for Hebron" },

  infoFeature1Title: { ar: "رصد مستويات الخزانات", en: "Tank Level Monitoring" },
  infoFeature1Desc: { ar: "مراقبة مستمرة لمستويات الخزانات عبر مستشعرات ذكية", en: "Continuous monitoring of tank levels via smart sensors" },

  infoFeature2Title: { ar: "تنبؤ قرب الفيضان", en: "Overflow Prediction" },
  infoFeature2Desc: { ar: "تحليل ذكي للتنبؤ بموعد امتلاء الخزانات", en: "Smart analysis to predict tank overflow times" },

  infoFeature3Title: { ar: "خطة جمع محسّنة", en: "Optimized Collection Plan" },
  infoFeature3Desc: { ar: "مسارات جمع محسّنة لتقليل المسافة والوقت والتكلفة", en: "Optimized collection routes to minimize distance, time, and cost" },

  infoFeature4Title: { ar: "تنبيهات فورية", en: "Real-time Alerts" },
  infoFeature4Desc: { ar: "إشعارات فورية عند اقتراب الخزانات من الفيضان", en: "Instant notifications when tanks approach overflow" },

  infoPriorityTitle: { ar: "مستويات الأولوية", en: "Priority Levels" },
  infoPriorityHigh: { ar: "عالي: يتطلب اهتماماً فورياً", en: "High: Requires immediate attention" },
  infoPriorityMedium: { ar: "متوسط: يجب الخدمة قريباً", en: "Medium: Should be serviced soon" },
  infoPriorityLow: { ar: "منخفض: وضع طبيعي", en: "Low: Normal status" },

  // Misc
  depot: { ar: "المركز", en: "Depot" },
  km: { ar: "كم", en: "km" },
  liters: { ar: "لتر", en: "L" },
  hours: { ar: "ساعة", en: "h" },
  minutes: { ar: "دقيقة", en: "min" },
  clearFocus: { ar: "عرض الكل", en: "Show All" },
  viewRoute: { ar: "عرض المسار", en: "View Route" },
  roadClosure: { ar: "إغلاق طريق", en: "Road Closure" },
  loading: { ar: "جاري التحميل...", en: "Loading..." },

  // Stats Tab
  tabStats: { ar: "الإحصائيات", en: "Statistics" },
  statsTitle: { ar: "الإحصائيات والرسوم البيانية", en: "Statistics & Charts" },
  statsSubtitle: { ar: "تحليل شامل لبيانات النظام والأداء", en: "Comprehensive analysis of system data and performance" },
  tierDistribution: { ar: "توزيع مستويات الأولوية", en: "Priority Tier Distribution" },
  levelDistribution: { ar: "توزيع نسب الامتلاء", en: "Fill Level Distribution" },
  ttoDistribution: { ar: "توزيع أوقات الفيضان", en: "Time to Overflow Distribution" },
  truckWorkload: { ar: "حمل العمل للشاحنات", en: "Truck Workload" },
  topPriorityTanks: { ar: "أعلى 10 خزانات أولوية", en: "Top 10 Priority Tanks" },
  weeklyTrend: { ar: "الاتجاه الأسبوعي", en: "Weekly Trend" },
  environmentalImpact: { ar: "التأثير البيئي والتكلفة", en: "Environmental Impact & Cost" },
  fuelCost: { ar: "تكلفة الوقود", en: "Fuel Cost" },
  efficiency: { ar: "الكفاءة", en: "Efficiency" },
  generatedCharts: { ar: "الرسوم البيانية المُولَّدة", en: "Generated Charts" },
  visualizations: { ar: "التصورات البصرية", en: "Visualizations" },
  tierCoverage: { ar: "تغطية المستويات", en: "Tier Coverage" },
  workloadBalance: { ar: "توازن حمل العمل", en: "Workload Balance" },
  distanceServed: { ar: "المسافة والخدمة", en: "Distance & Served" },
  efficiencySafety: { ar: "الكفاءة مقابل السلامة", en: "Efficiency vs Safety" },
  routesCompare: { ar: "مقارنة المسارات", en: "Routes Comparison" },
  forecastViz: { ar: "التنبؤ", en: "Forecast" },
  priorityWow: { ar: "تغير الأولوية", en: "Priority Change" },
  priorityBreakdown: { ar: "تفصيل الأولوية", en: "Priority Breakdown" },
  routesBeforeAfter: { ar: "المسارات قبل وبعد", en: "Routes Before & After" },
  kpisViz: { ar: "مؤشرات الأداء", en: "KPIs" }
};

export function t(key: keyof typeof translations, lang: Language): string {
  return translations[key]?.[lang] ?? key;
}

interface InfoTabProps {
  t: (key: string) => string;
}

export default function InfoTab({ t }: InfoTabProps) {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="panel p-6 text-center">
        <img src="/logo/RASD.png" alt="RASD" className="h-24 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-neon-cyan">{t("infoTitle")}</h1>
        <p className="text-slate-400 mt-2">{t("infoDesc")}</p>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="panel p-5">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">📊</span>
            <h3 className="text-lg font-bold">{t("infoFeature1Title")}</h3>
          </div>
          <p className="text-sm text-slate-400">{t("infoFeature1Desc")}</p>
        </div>

        <div className="panel p-5">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">⏰</span>
            <h3 className="text-lg font-bold">{t("infoFeature2Title")}</h3>
          </div>
          <p className="text-sm text-slate-400">{t("infoFeature2Desc")}</p>
        </div>

        <div className="panel p-5">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">🛣️</span>
            <h3 className="text-lg font-bold">{t("infoFeature3Title")}</h3>
          </div>
          <p className="text-sm text-slate-400">{t("infoFeature3Desc")}</p>
        </div>

        <div className="panel p-5">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">🚨</span>
            <h3 className="text-lg font-bold">{t("infoFeature4Title")}</h3>
          </div>
          <p className="text-sm text-slate-400">{t("infoFeature4Desc")}</p>
        </div>
      </div>

      {/* Priority Levels */}
      <div className="panel p-6">
        <h3 className="text-lg font-bold mb-4">{t("infoPriorityTitle")}</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3 panel-soft p-3 rounded-lg border border-red-500/30">
            <span className="h-4 w-4 rounded-full bg-red-500"></span>
            <span className="text-red-400 font-bold">{t("tierHigh")}</span>
            <span className="text-slate-400">- {t("infoPriorityHigh")}</span>
          </div>
          <div className="flex items-center gap-3 panel-soft p-3 rounded-lg border border-yellow-500/30">
            <span className="h-4 w-4 rounded-full bg-yellow-500"></span>
            <span className="text-yellow-400 font-bold">{t("tierMedium")}</span>
            <span className="text-slate-400">- {t("infoPriorityMedium")}</span>
          </div>
          <div className="flex items-center gap-3 panel-soft p-3 rounded-lg border border-green-500/30">
            <span className="h-4 w-4 rounded-full bg-green-500"></span>
            <span className="text-green-400 font-bold">{t("tierLow")}</span>
            <span className="text-slate-400">- {t("infoPriorityLow")}</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-sm text-slate-500 py-4">
        <p>نظام RASD - إدارة جمع النفايات الذكية</p>
        <p className="mt-1">الإصدار 1.0 - 2026</p>
      </div>
    </div>
  );
}

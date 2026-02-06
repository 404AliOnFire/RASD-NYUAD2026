interface TabItem {
  key: string;
  label: string;
}

interface TabsProps {
  active: string;
  setActive: (tab: string) => void;
  tabs: TabItem[];
}

export default function Tabs({ active, setActive, tabs }: TabsProps) {
  return (
    <div className="flex gap-2 flex-wrap">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => setActive(tab.key)}
          className={`px-4 py-2 rounded-full border text-sm transition ${
            active === tab.key
              ? "bg-neon-cyan text-black border-neon-cyan shadow-glow font-semibold"
              : "bg-panel-soft text-slate-300 border-grid hover:border-neon-cyan"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

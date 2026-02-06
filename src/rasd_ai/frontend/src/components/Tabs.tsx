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
    <div className="overflow-x-auto hide-scrollbar -mx-2 px-2">
      <div className="flex gap-1 md:gap-2 min-w-max">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActive(tab.key)}
            className={`px-3 md:px-4 py-1.5 md:py-2 rounded-full border text-xs md:text-sm transition whitespace-nowrap ${
              active === tab.key
                ? "bg-neon-cyan text-black border-neon-cyan shadow-glow font-semibold"
                : "bg-panel-soft text-slate-300 border-grid hover:border-neon-cyan"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}

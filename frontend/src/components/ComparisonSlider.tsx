import { useState } from "react";

type ComparisonSliderProps = {
  beforeUrl: string;
  afterUrl: string;
  beforeLabel: string;
  afterLabel: string;
};

export function ComparisonSlider({
  beforeUrl,
  afterUrl,
  beforeLabel,
  afterLabel,
}: ComparisonSliderProps) {
  const [position, setPosition] = useState(52);

  return (
    <div className="overflow-hidden rounded-[1.75rem] border border-white/70 bg-white p-4 shadow-float">
      <div className="relative h-80 overflow-hidden rounded-[1.25rem] bg-slate-100">
        <img src={afterUrl} alt={afterLabel} className="h-full w-full object-contain" />
        <div
          className="absolute inset-y-0 left-0 overflow-hidden border-r-2 border-white"
          style={{ width: `${position}%` }}
        >
          <img src={beforeUrl} alt={beforeLabel} className="h-full w-full object-contain bg-slate-100" />
        </div>
        <div
          className="absolute inset-y-0 w-1 bg-white/90 shadow-lg"
          style={{ left: `calc(${position}% - 2px)` }}
        />
      </div>
      <div className="mt-4 flex items-center gap-4">
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          {beforeLabel}
        </span>
        <input
          type="range"
          min={0}
          max={100}
          value={position}
          onChange={(event) => setPosition(Number(event.target.value))}
          className="w-full accent-slate-900"
        />
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          {afterLabel}
        </span>
      </div>
    </div>
  );
}

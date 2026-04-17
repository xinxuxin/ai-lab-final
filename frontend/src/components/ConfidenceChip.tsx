type ConfidenceChipProps = {
  label: string;
  value: number;
};

export function ConfidenceChip({ label, value }: ConfidenceChipProps) {
  const percentage = Math.round(value * 100);
  const tone =
    percentage >= 85
      ? "border-lime-200 bg-lime-50 text-lime-700"
      : percentage >= 70
        ? "border-sky-200 bg-sky-50 text-sky-700"
        : "border-orange-200 bg-orange-50 text-orange-700";

  return (
    <div className={`rounded-2xl border px-3 py-2 ${tone}`}>
      <p className="text-xs uppercase tracking-[0.18em]">{label}</p>
      <p className="mt-1 font-semibold">{percentage}% confidence</p>
    </div>
  );
}


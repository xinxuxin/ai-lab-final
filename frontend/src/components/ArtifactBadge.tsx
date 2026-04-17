type ArtifactBadgeProps = {
  label: string;
  tone?: "neutral" | "sky" | "lime" | "coral";
};

const toneClasses: Record<NonNullable<ArtifactBadgeProps["tone"]>, string> = {
  neutral: "border-slate-200 bg-slate-50 text-slate-600",
  sky: "border-sky-200 bg-sky-50 text-sky-700",
  lime: "border-lime-200 bg-lime-50 text-lime-700",
  coral: "border-orange-200 bg-orange-50 text-orange-700",
};

export function ArtifactBadge({ label, tone = "neutral" }: ArtifactBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${toneClasses[tone]}`}
    >
      {label}
    </span>
  );
}

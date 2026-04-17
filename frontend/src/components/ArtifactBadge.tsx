type ArtifactBadgeProps = {
  label: string;
};

export function ArtifactBadge({ label }: ArtifactBadgeProps) {
  return (
    <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
      {label}
    </span>
  );
}


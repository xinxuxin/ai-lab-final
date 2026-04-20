type MissingArtifactStateProps = {
  title: string;
  message: string;
  details?: string[];
};

export function MissingArtifactState({
  title,
  message,
  details = [],
}: MissingArtifactStateProps) {
  return (
    <div className="rounded-[1.75rem] border border-orange-200 bg-orange-50 p-6 shadow-float">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-orange-700">
        Missing Artifact State
      </p>
      <h3 className="mt-3 font-display text-3xl font-semibold text-ink">{title}</h3>
      <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-700">{message}</p>
      {details.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {details.map((detail) => (
            <span
              key={detail}
              className="rounded-full border border-orange-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-orange-700"
            >
              {detail}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

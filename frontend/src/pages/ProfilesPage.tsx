import { AnimatedSection } from "../components/AnimatedSection";
import { promptVersions } from "../data/mockData";

export function ProfilesPage() {
  return (
    <AnimatedSection
      eyebrow="Q2"
      title="Visual profile extraction"
      description="This space is reserved for evidence-backed attributes, materials, colors, and packaging cues extracted through prompt-engineered LLM analysis."
    >
      <div className="grid gap-5 lg:grid-cols-3">
        {promptVersions.map((item) => (
          <article
            key={item.version}
            className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
          >
            <p className="text-sm uppercase tracking-[0.2em] text-slate-500">{item.version}</p>
            <h3 className="mt-3 font-display text-2xl font-semibold text-ink">{item.strategy}</h3>
            <p className="mt-4 text-sm leading-6 text-slate-600">{item.summary}</p>
          </article>
        ))}
      </div>
    </AnimatedSection>
  );
}


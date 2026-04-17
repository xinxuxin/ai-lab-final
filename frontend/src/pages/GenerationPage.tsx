import { AnimatedSection } from "../components/AnimatedSection";
import { ImageGrid } from "../components/ImageGrid";
import { imagePlaceholders, promptVersions } from "../data/mockData";

export function GenerationPage() {
  return (
    <AnimatedSection
      eyebrow="Q3"
      title="Prompt versions and generated images"
      description="The production version will show provider-level prompt lineage, generated images per product, failures, retries, and parameter differences."
    >
      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        {promptVersions.map((item) => (
          <div
            key={item.version}
            className="rounded-[1.5rem] border border-white/70 bg-white px-5 py-4 shadow-float"
          >
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{item.version}</p>
            <p className="mt-2 font-semibold text-ink">{item.strategy}</p>
            <p className="mt-2 text-sm text-slate-600">{item.summary}</p>
          </div>
        ))}
      </div>
      <ImageGrid items={imagePlaceholders} />
    </AnimatedSection>
  );
}


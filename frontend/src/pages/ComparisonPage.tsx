import { AnimatedSection } from "../components/AnimatedSection";
import { ImageGrid } from "../components/ImageGrid";
import { imagePlaceholders } from "../data/mockData";

export function ComparisonPage() {
  return (
    <AnimatedSection
      eyebrow="Q3"
      title="Generated image comparison"
      description="This presentation page will pair reference product photos with outputs from multiple models and summarize similarity, differences, and likely prompt causes."
    >
      <ImageGrid items={imagePlaceholders} />
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        {[
          "Similarity: packaging silhouette and main material aligned with reviews.",
          "Difference: lighting and studio styling may drift from marketplace photos.",
          "Model effect: one provider may preserve texture, while another emphasizes composition cleanliness.",
        ].map((note) => (
          <div
            key={note}
            className="rounded-[1.5rem] border border-white/70 bg-white px-5 py-4 text-sm text-slate-600 shadow-float"
          >
            {note}
          </div>
        ))}
      </div>
    </AnimatedSection>
  );
}


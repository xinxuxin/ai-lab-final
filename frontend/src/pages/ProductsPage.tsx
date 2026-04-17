import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { productCards } from "../data/mockData";

export function ProductsPage() {
  return (
    <AnimatedSection
      eyebrow="Q1"
      title="Product selection"
      description="This page will eventually show candidate discovery, category spread, popularity balancing, and the rationale for the final three selected products."
    >
      <div className="grid gap-5 lg:grid-cols-3">
        {productCards.map((product) => (
          <article
            key={product.title}
            className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
          >
            <div className="flex items-center justify-between gap-4">
              <h3 className="font-display text-2xl font-semibold text-ink">{product.title}</h3>
              <ArtifactBadge label={product.popularity} />
            </div>
            <p className="mt-3 text-sm uppercase tracking-[0.18em] text-slate-500">
              {product.category}
            </p>
            <p className="mt-5 text-sm leading-6 text-slate-600">{product.note}</p>
          </article>
        ))}
      </div>
    </AnimatedSection>
  );
}


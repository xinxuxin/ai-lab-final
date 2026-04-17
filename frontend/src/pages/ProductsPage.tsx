import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { PageHeader } from "../components/PageHeader";
import { StatCard } from "../components/StatCard";
import { productStatHighlights, selectedProducts } from "../mock/projectData";

export function ProductsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Q1 Product Selection"
        title="Three products chosen for category spread and evidence quality"
        description="The demo already shows the exact structure we need for the final report: product cards, category badges, popularity signals, review counts, and rationale for why each product belongs in the study."
        badges={["3 final products", "category diversity", "popularity balancing"]}
      />

      <div className="grid gap-4 md:grid-cols-3">
        {productStatHighlights.map((item, index) => (
          <StatCard
            key={item.label}
            label={item.label}
            value={item.value}
            hint="Selection logic visible for presentation"
            accent={["from-white to-sky-50", "from-white to-orange-50", "from-white to-lime-50"][index]}
          />
        ))}
      </div>

      <AnimatedSection
        title="Selected product cards"
        description="Each card combines category fit, popularity level, review count, and a concise rationale so the UI can later point directly to supporting artifacts."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          {selectedProducts.map((product) => (
            <article
              key={product.id}
              className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-display text-2xl font-semibold text-ink">{product.title}</h3>
                  <p className="mt-2 text-sm text-slate-500">{product.categoryFit}</p>
                </div>
                <ArtifactBadge label={product.category} tone="sky" />
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-2xl bg-slate-50 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Popularity</p>
                  <p className="mt-2 font-semibold text-ink">{product.popularity}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Review count</p>
                  <p className="mt-2 font-semibold text-ink">{product.reviewCount}</p>
                </div>
              </div>
              <div className="mt-5 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Rationale</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{product.rationale}</p>
              </div>
              <div className="mt-4 rounded-[1.5rem] border border-sky-100 bg-sky-50 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Visual hook</p>
                <p className="mt-2 text-sm leading-6 text-slate-700">{product.visualHook}</p>
              </div>
            </article>
          ))}
        </div>
      </AnimatedSection>
    </>
  );
}

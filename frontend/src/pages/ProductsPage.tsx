import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { FreshnessBadge } from "../components/FreshnessBadge";
import { LoadingState } from "../components/LoadingState";
import { MissingArtifactState } from "../components/MissingArtifactState";
import { PageHeader } from "../components/PageHeader";
import { StatCard } from "../components/StatCard";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";

export function ProductsPage() {
  const productsQuery = useApiData(() => api.getProducts(), []);

  if (productsQuery.loading && !productsQuery.data) {
    return <LoadingState title="Loading selected products" lines={5} />;
  }

  if (productsQuery.error || productsQuery.data?.status === "missing_artifact") {
    return (
      <MissingArtifactState
        title="Product corpus is not ready"
        message={
          productsQuery.error ??
          productsQuery.data?.message ??
          "Run build-corpus so the frontend can read processed product artifacts."
        }
      />
    );
  }

  const products = productsQuery.data?.items ?? [];
  const productStatHighlights = [
    {
      label: "Category coverage",
      value: Array.from(new Set(products.map((item) => item.category))).join(" / "),
    },
    {
      label: "Review pool",
      value: String(products.reduce((sum, item) => sum + item.reviewCount, 0)),
    },
    {
      label: "Ready profiles",
      value: String(
        products.filter(
          (item) => item.artifacts.profiles.baseline && item.artifacts.profiles.reviewInformed,
        ).length,
      ),
    },
  ];

  return (
    <>
      <PageHeader
        eyebrow="Q1 Product Selection"
        title="Three products chosen for category spread and evidence quality"
        description="These cards are now loaded from the real processed corpus and selected-product manifest, so the presentation reflects the actual study setup."
        badges={["3 final products", "category diversity", "artifact-backed"]}
      />

      <div className="grid gap-4 md:grid-cols-3">
        {productStatHighlights.map((item, index) => (
          <StatCard
            key={item.label}
            label={item.label}
            value={item.value}
            hint="Loaded from processed and selected-product artifacts"
            accent={
              ["from-white to-sky-50", "from-white to-orange-50", "from-white to-lime-50"][
                index
              ]
            }
          />
        ))}
      </div>

      <AnimatedSection
        title="Selected product cards"
        description="Each card shows the stored rationale, artifact coverage, and freshness for the final three products."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          {products.map((product) => (
            <article
              key={product.slug}
              className="overflow-hidden rounded-[1.75rem] border border-white/70 bg-white shadow-float"
            >
              <div className="h-52 bg-slate-100">
                {product.primaryImageUrl ? (
                  <img
                    src={product.primaryImageUrl}
                    alt={product.title}
                    className="h-full w-full object-contain p-4"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-slate-400">
                    Missing reference image
                  </div>
                )}
              </div>
              <div className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-display text-2xl font-semibold text-ink">{product.title}</h3>
                    <p className="mt-2 text-sm text-slate-500">{product.selectedCategory}</p>
                  </div>
                  <ArtifactBadge label={product.category} tone="sky" />
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3">
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                      Popularity
                    </p>
                    <p className="mt-2 font-semibold text-ink">{product.popularityHint ?? "n/a"}</p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                      Review count
                    </p>
                    <p className="mt-2 font-semibold text-ink">{product.reviewCount}</p>
                  </div>
                </div>
                <div className="mt-5 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Rationale</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {product.rationale ?? "No rationale saved yet."}
                  </p>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <ArtifactBadge
                    label={product.artifacts.profiles.reviewInformed ? "profiles ready" : "profiles partial"}
                    tone={product.artifacts.profiles.reviewInformed ? "lime" : "coral"}
                  />
                  <ArtifactBadge
                    label={product.artifacts.evaluation ? "evaluation ready" : "evaluation missing"}
                    tone={product.artifacts.evaluation ? "lime" : "neutral"}
                  />
                  <FreshnessBadge value={product.freshness.processed} label="processed" />
                </div>
              </div>
            </article>
          ))}
        </div>
      </AnimatedSection>
    </>
  );
}

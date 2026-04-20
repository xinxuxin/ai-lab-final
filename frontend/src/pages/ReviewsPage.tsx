import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { FreshnessBadge } from "../components/FreshnessBadge";
import { LoadingState } from "../components/LoadingState";
import { MissingArtifactState } from "../components/MissingArtifactState";
import { PageHeader } from "../components/PageHeader";
import { ProductSelector } from "../components/ProductSelector";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";

export function ReviewsPage() {
  const productsQuery = useApiData(() => api.getProducts(), []);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedSlug && productsQuery.data?.items?.length) {
      setSelectedSlug(productsQuery.data.items[0].slug);
    }
  }, [productsQuery.data, selectedSlug]);

  const reviewsQuery = useApiData(
    () => api.getReviews(selectedSlug ?? ""),
    [selectedSlug],
    { enabled: Boolean(selectedSlug) },
  );

  if (productsQuery.loading && !productsQuery.data) {
    return <LoadingState title="Loading review explorer data" lines={5} />;
  }

  const products = productsQuery.data?.items ?? [];
  const reviewVolume = products.map((product) => ({
    product: product.title,
    reviews: product.reviewCount,
    visibleReviews: product.visibleReviewCount ?? product.reviewCount,
  }));

  return (
    <>
      <PageHeader
        eyebrow="Review Explorer"
        title="Review evidence, chunking, and retrieval in one presentation view"
        description="The review page now reads real review stats, sampled cleaned reviews, and saved retrieval evidence where available."
        badges={["review chart", "retrieved evidence", "real artifacts"]}
      />

      <ProductSelector
        products={products}
        selectedSlug={selectedSlug}
        onSelect={setSelectedSlug}
      />

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <AnimatedSection
          title="Review count and cleaned corpus coverage"
          description="This chart compares cleaned review counts to visible marketplace review counts."
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={reviewVolume}>
                <CartesianGrid strokeDasharray="4 4" stroke="#d7dfed" />
                <XAxis dataKey="product" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip />
                <Bar dataKey="reviews" fill="#8ec5ff" radius={[10, 10, 0, 0]} />
                <Bar dataKey="visibleReviews" fill="#ff8a72" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </AnimatedSection>

        <AnimatedSection
          title="Chunking and retrieval method"
          description="Chunking remains one-review-first, with retrieval evidence saved to disk whenever visual profile extraction has already been run."
        >
          <div className="space-y-4">
            <div className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-600">
              Reviews are cleaned once, then reused as the default source for downstream Q2
              retrieval and prompt construction.
            </div>
            <div className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-600">
              Retrieval evidence shown below comes from saved `retrieval_evidence.json` artifacts and
              will stay empty when a product has not completed Q2 yet.
            </div>
            <FreshnessBadge value={reviewsQuery.data?.freshness?.retrieval} label="retrieval" />
          </div>
        </AnimatedSection>
      </div>

      <AnimatedSection
        title="Sample review cards"
        description="Sampled cleaned reviews are pulled from the processed corpus for the selected product."
      >
        {reviewsQuery.loading ? (
          <LoadingState title="Loading review samples" lines={4} />
        ) : reviewsQuery.data?.status === "missing_artifact" ? (
          <MissingArtifactState
            title="Review artifacts missing"
            message={reviewsQuery.data.message ?? "No processed review corpus was found."}
          />
        ) : (
          <div className="grid gap-5 lg:grid-cols-3">
            {(reviewsQuery.data?.samples ?? []).map((review) => (
              <article
                key={String(review.review_id)}
                className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
              >
                <div className="flex items-center justify-between gap-3">
                  <ArtifactBadge
                    label={String(review.rating ?? "n/a")}
                    tone="coral"
                  />
                  <FreshnessBadge value={String(review.posted_at ?? "")} label="posted" />
                </div>
                <h3 className="mt-4 font-display text-2xl font-semibold text-ink">
                  {String(review.title ?? "Untitled review")}
                </h3>
                <p className="mt-4 text-sm leading-6 text-slate-600">{String(review.body ?? "")}</p>
              </article>
            ))}
          </div>
        )}
      </AnimatedSection>

      <AnimatedSection
        title="Retrieved evidence panels"
        description="These evidence snippets come from saved retrieval artifacts used during visual-profile extraction."
      >
        {reviewsQuery.loading ? (
          <LoadingState title="Loading evidence snippets" lines={3} />
        ) : (reviewsQuery.data?.evidenceSnippets ?? []).length ? (
          <div className="grid gap-5 lg:grid-cols-3">
            {(reviewsQuery.data?.evidenceSnippets ?? []).map((panel, index) => (
              <article
                key={`${panel.mode}-${panel.aspect}-${index}`}
                className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
              >
                <div className="flex flex-wrap gap-2">
                  <ArtifactBadge label={panel.mode} tone="sky" />
                  <ArtifactBadge label={panel.aspect} tone="neutral" />
                </div>
                <p className="mt-4 text-sm italic leading-6 text-slate-700">{panel.snippet}</p>
                <p className="mt-4 text-sm leading-6 text-slate-600">
                  Retrieval score: {panel.score?.toFixed?.(2) ?? panel.score}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <MissingArtifactState
            title="No saved retrieval evidence yet"
            message="This product does not have retrieval evidence on disk yet. Run extract-visual-profile in review-informed mode to populate this panel."
          />
        )}
      </AnimatedSection>
    </>
  );
}

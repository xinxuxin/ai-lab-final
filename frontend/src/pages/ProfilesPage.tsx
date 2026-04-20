import { useEffect, useMemo, useState } from "react";
import { AnimatedSection } from "../components/AnimatedSection";
import { ConfidenceChip } from "../components/ConfidenceChip";
import { FreshnessBadge } from "../components/FreshnessBadge";
import { LoadingState } from "../components/LoadingState";
import { MissingArtifactState } from "../components/MissingArtifactState";
import { PageHeader } from "../components/PageHeader";
import { ProductSelector } from "../components/ProductSelector";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";

export function ProfilesPage() {
  const productsQuery = useApiData(() => api.getProducts(), []);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [activeMode, setActiveMode] = useState<"baseline_description_only" | "review_informed_rag">(
    "review_informed_rag",
  );

  useEffect(() => {
    if (!selectedSlug && productsQuery.data?.items?.length) {
      const preferred =
        productsQuery.data.items.find((item) => item.artifacts.profiles.reviewInformed) ??
        productsQuery.data.items[0];
      setSelectedSlug(preferred.slug);
    }
  }, [productsQuery.data, selectedSlug]);

  const profilesQuery = useApiData(
    () => api.getProfiles(selectedSlug ?? ""),
    [selectedSlug],
    { enabled: Boolean(selectedSlug) },
  );

  const activeProfile = useMemo(() => {
    if (!profilesQuery.data) {
      return null;
    }
    return profilesQuery.data.modes[activeMode];
  }, [activeMode, profilesQuery.data]);

  return (
    <>
      <PageHeader
        eyebrow="Visual Profile"
        title="Structured attributes extracted from review evidence"
        description="This page shows baseline versus review-informed profiles, confidence-bearing attributes, conflicts, and the prompt-ready description that feeds Q3."
        badges={["baseline vs review-informed", "confidence", "prompt-ready output"]}
      />

      <ProductSelector
        products={productsQuery.data?.items ?? []}
        selectedSlug={selectedSlug}
        onSelect={setSelectedSlug}
      />

      <AnimatedSection
        title="Profile mode switcher"
        description="Switch between the baseline description-only profile and the review-informed RAG profile."
      >
        <div className="flex flex-wrap gap-3">
          {(["baseline_description_only", "review_informed_rag"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setActiveMode(mode)}
              className={`rounded-full px-5 py-3 text-sm font-semibold transition ${
                activeMode === mode
                  ? "bg-ink text-white shadow-float"
                  : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
              }`}
            >
              {mode}
            </button>
          ))}
          <FreshnessBadge value={activeProfile?.updatedAt} label="profile" />
        </div>
      </AnimatedSection>

      {profilesQuery.loading ? (
        <LoadingState title="Loading saved visual profiles" lines={5} />
      ) : activeProfile?.status === "missing_artifact" || !activeProfile?.profile ? (
        <MissingArtifactState
          title="Visual profile artifact missing"
          message={
            activeProfile?.message ??
            "This product does not have the selected profile mode on disk yet."
          }
          details={profilesQuery.data?.missingArtifacts}
        />
      ) : (
        <>
          <AnimatedSection
            title="Structured extracted attributes"
            description="Attributes are grouped by confidence so the presentation can separate grounded details from uncertain ones."
          >
            <div className="grid gap-5 lg:grid-cols-2">
              <article className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float">
                <h3 className="font-display text-2xl font-semibold text-ink">High confidence</h3>
                <div className="mt-5 space-y-4">
                  {activeProfile.profile.high_confidence_visual_attributes.map((item) => (
                    <div
                      key={item.attribute}
                      className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4"
                    >
                      <p className="font-medium text-ink">{item.attribute}</p>
                      <div className="mt-3">
                        <ConfidenceChip label="evidence confidence" value={0.9} />
                      </div>
                      <p className="mt-3 text-sm leading-6 text-slate-600">{item.rationale}</p>
                    </div>
                  ))}
                </div>
              </article>
              <article className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float">
                <h3 className="font-display text-2xl font-semibold text-ink">Lower confidence</h3>
                <div className="mt-5 space-y-4">
                  {activeProfile.profile.low_confidence_or_conflicting_attributes.map((item) => (
                    <div
                      key={item.attribute}
                      className="rounded-[1.25rem] border border-orange-100 bg-orange-50 px-4 py-4"
                    >
                      <p className="font-medium text-ink">{item.attribute}</p>
                      <div className="mt-3">
                        <ConfidenceChip label="uncertain" value={0.45} />
                      </div>
                      <p className="mt-3 text-sm leading-6 text-slate-600">{item.rationale}</p>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </AnimatedSection>

          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <AnimatedSection
              title="Conflicting attributes"
              description="Any uncertainty preserved in Q2 stays visible instead of being hidden before image generation."
            >
              <div className="space-y-4">
                {activeProfile.profile.common_mismatches_between_expectation_and_reality.length ? (
                  activeProfile.profile.common_mismatches_between_expectation_and_reality.map((item) => (
                    <div
                      key={item.mismatch}
                      className="rounded-[1.5rem] border border-orange-100 bg-orange-50 p-5"
                    >
                      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-orange-700">
                        expectation vs reality
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-700">{item.mismatch}</p>
                    </div>
                  ))
                ) : (
                  <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5 text-sm leading-6 text-slate-600">
                    No explicit mismatch artifacts were saved for this product and mode.
                  </div>
                )}
              </div>
            </AnimatedSection>

            <AnimatedSection
              title="Prompt-ready description"
              description="This is the exact profile text prepared for downstream image generation."
            >
              <div className="rounded-[1.75rem] border border-slate-200 bg-slate-950 p-6 text-slate-100 shadow-inner">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">prompt-ready profile</p>
                <p className="mt-4 text-sm leading-7 text-slate-200">
                  {activeProfile.profile.prompt_ready_description}
                </p>
                <div className="mt-5 flex flex-wrap gap-2">
                  {activeProfile.profile.negative_constraints.map((constraint) => (
                    <span
                      key={constraint}
                      className="rounded-full border border-slate-700 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-300"
                    >
                      {constraint}
                    </span>
                  ))}
                </div>
              </div>
            </AnimatedSection>
          </div>
        </>
      )}
    </>
  );
}

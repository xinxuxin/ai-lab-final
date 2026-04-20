import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { ComparisonSlider } from "../components/ComparisonSlider";
import { FreshnessBadge } from "../components/FreshnessBadge";
import { LoadingState } from "../components/LoadingState";
import { MissingArtifactState } from "../components/MissingArtifactState";
import { PageHeader } from "../components/PageHeader";
import { ProductSelector } from "../components/ProductSelector";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";

export function ComparisonPage() {
  const productsQuery = useApiData(() => api.getProducts(), []);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedSlug && productsQuery.data?.items?.length) {
      const preferred =
        productsQuery.data.items.find((item) => item.artifacts.evaluation) ??
        productsQuery.data.items[0];
      setSelectedSlug(preferred.slug);
    }
  }, [productsQuery.data, selectedSlug]);

  const evaluationQuery = useApiData(
    () => api.getEvaluation(selectedSlug ?? ""),
    [selectedSlug],
    { enabled: Boolean(selectedSlug) },
  );

  const scoreChartData = useMemo(() => {
    const aggregate = evaluationQuery.data?.summary?.aggregate_scores ?? {};
    const dimensions = [
      "color_accuracy",
      "material_finish_accuracy",
      "shape_silhouette_accuracy",
      "component_completeness",
      "size_proportion_impression",
      "overall_recognizability",
    ];
    return dimensions.map((dimension) => ({
      metric: dimension.replace(/_/g, " "),
      openai: aggregate.openai?.[dimension] ?? 0,
      stability: aggregate.stability?.[dimension] ?? 0,
    }));
  }, [evaluationQuery.data]);

  const hasAggregateScores = useMemo(
    () => scoreChartData.some((item) => item.openai > 0 || item.stability > 0),
    [scoreChartData],
  );

  const firstPanel = evaluationQuery.data?.comparisonPanels?.[0];

  return (
    <>
      <PageHeader
        eyebrow="Comparison Dashboard"
        title="Reference versus generated image evaluation"
        description="This page compares real reference images with generated outputs and surfaces per-dimension scoring, summary text, and model-level differences when evaluation artifacts exist."
        badges={["reference vs generated", "score charts", "model summary"]}
      />

      <ProductSelector
        products={productsQuery.data?.items ?? []}
        selectedSlug={selectedSlug}
        onSelect={setSelectedSlug}
      />

      {evaluationQuery.loading ? (
        <LoadingState title="Loading evaluation artifacts" lines={5} />
      ) : evaluationQuery.data?.status === "missing_artifact" ? (
        <MissingArtifactState
          title="Evaluation artifacts missing"
          message={
            evaluationQuery.data.message ??
            "Run evaluate-images after generation artifacts exist."
          }
        />
      ) : (
        <>
          <AnimatedSection
            title="Interactive comparison"
            description="Use the slider to compare a real product reference with one generated candidate."
          >
            <div className="mb-4 flex flex-wrap gap-2">
              <FreshnessBadge value={evaluationQuery.data?.freshness} label="evaluation" />
              <ArtifactBadge
                label={evaluationQuery.data?.summary?.vision_assisted_status ?? "not_run"}
                tone={
                  evaluationQuery.data?.summary?.vision_assisted_status === "completed"
                    ? "lime"
                    : "coral"
                }
              />
            </div>
            {firstPanel ? (
              <ComparisonSlider
                beforeUrl={firstPanel.referenceImageUrl}
                afterUrl={firstPanel.generatedImageUrl}
                beforeLabel="Reference"
                afterLabel={`${firstPanel.provider} generated`}
              />
            ) : (
              <MissingArtifactState
                title="No comparison panels available"
                message="The evaluation summary exists, but no saved comparison panels were found."
              />
            )}
          </AnimatedSection>

          <AnimatedSection
            title="Side-by-side panel gallery"
            description="Every saved comparison panel is preserved for report screenshots and UI browsing."
          >
            <div className="grid gap-5 lg:grid-cols-2">
              {(evaluationQuery.data?.comparisonPanels ?? []).map((panel) => (
                <div
                  key={panel.panel_id}
                  className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
                >
                  <div className="flex flex-wrap gap-2">
                    <ArtifactBadge label={panel.provider} tone="sky" />
                    <ArtifactBadge label={panel.prompt_source_mode} tone="neutral" />
                  </div>
                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    <img
                      src={panel.referenceImageUrl}
                      alt="Reference product"
                      className="h-56 w-full rounded-[1.25rem] bg-slate-100 object-contain"
                    />
                    <img
                      src={panel.generatedImageUrl}
                      alt="Generated product"
                      className="h-56 w-full rounded-[1.25rem] bg-slate-100 object-contain"
                    />
                  </div>
                </div>
              ))}
            </div>
          </AnimatedSection>

          <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
            <AnimatedSection
              title="Per-dimension scores"
              description="Bar charts summarize provider averages whenever vision-assisted evaluation has been run."
            >
              {hasAggregateScores ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={scoreChartData}>
                      <CartesianGrid strokeDasharray="4 4" stroke="#d7dfed" />
                      <XAxis dataKey="metric" stroke="#64748b" />
                      <YAxis stroke="#64748b" domain={[0, 5]} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="openai" fill="#8ec5ff" radius={[10, 10, 0, 0]} />
                      <Bar dataKey="stability" fill="#ff8a72" radius={[10, 10, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <MissingArtifactState
                  title="Vision-assisted scores unavailable"
                  message={
                    typeof evaluationQuery.data?.visionAssisted?.reason === "string"
                      ? `No aggregate score chart is available for this product yet. Latest reason: ${evaluationQuery.data.visionAssisted.reason}`
                      : "No aggregate score chart is available for this product yet. The side-by-side panels and saved evaluation summary are still available below."
                  }
                />
              )}
            </AnimatedSection>

            <AnimatedSection
              title="Radar view"
              description="The radar view summarizes provider tradeoffs across the evaluation rubric."
            >
              {hasAggregateScores ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={scoreChartData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="metric" />
                      <PolarRadiusAxis domain={[0, 5]} />
                      <Radar dataKey="openai" stroke="#0ea5e9" fill="#8ec5ff" fillOpacity={0.35} />
                      <Radar dataKey="stability" stroke="#f97316" fill="#ff8a72" fillOpacity={0.22} />
                      <Tooltip />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <MissingArtifactState
                  title="Radar comparison unavailable"
                  message="This view appears after provider-level aggregate scores have been saved. The product still has real comparison panels and summary text below."
                />
              )}
            </AnimatedSection>
          </div>

          <AnimatedSection
            title="Summary text"
            description="This text is loaded from the saved evaluation summary artifact."
          >
            <div className="grid gap-5 lg:grid-cols-3">
              <article className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float lg:col-span-2">
                <h3 className="font-display text-2xl font-semibold text-ink">
                  {evaluationQuery.data?.summary?.product_name}
                </h3>
                <p className="mt-4 text-sm leading-6 text-slate-600">
                  {evaluationQuery.data?.summary?.summary_text}
                </p>
              </article>
              <article className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">model coverage</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {(evaluationQuery.data?.summary?.available_models ?? []).map((model) => (
                    <ArtifactBadge key={model} label={model} tone="lime" />
                  ))}
                  {(evaluationQuery.data?.summary?.missing_models ?? []).map((model) => (
                    <ArtifactBadge key={model} label={`${model} missing`} tone="coral" />
                  ))}
                </div>
              </article>
            </div>
          </AnimatedSection>
        </>
      )}
    </>
  );
}

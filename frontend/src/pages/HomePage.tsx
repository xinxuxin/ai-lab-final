import { motion } from "framer-motion";
import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { LoadingState } from "../components/LoadingState";
import { StageCard } from "../components/StageCard";
import { StatCard } from "../components/StatCard";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";
import { rubricItems } from "../lib/presentation";

const shortProductNames: Record<string, string> = {
  "jbl-tour-one-m2-wireless-over-ear-adaptive-noise-cancelling-headphones-black-89301002":
    "JBL Tour One M2",
  "levoit-core-300-air-purifier-white-81910071": "Levoit Core 300",
  "desk-lamp-with-usb-ports-includes-led-light-bulb-threshold-8482-80705997":
    "Threshold Desk Lamp",
};

const stagePresentation: Record<
  string,
  {
    title: string;
    description: string;
    artifactLabel: string;
  }
> = {
  data_curation: {
    title: "Q1 Data Curation",
    description: "Three selected products, cleaned descriptions, reviews, and reference images.",
    artifactLabel: "Processed corpus",
  },
  retrieval: {
    title: "Q2 Retrieval",
    description: "Aspect-based evidence retrieval across appearance, color, material, size, and mismatch signals.",
    artifactLabel: "Evidence trace",
  },
  visual_understanding: {
    title: "Q2 Visual Profile",
    description: "Baseline and review-informed visual profiles synthesized into prompt-ready structure.",
    artifactLabel: "Visual profiles",
  },
  prompt_composition: {
    title: "Q3 Prompt Design",
    description: "Pilot and refined prompts composed from grounded visual attributes.",
    artifactLabel: "Prompt versions",
  },
  image_generation: {
    title: "Q3 Generation",
    description: "Dual-model image generation with OpenAI and Stability across all products.",
    artifactLabel: "Image manifests",
  },
  evaluation: {
    title: "Q4 Evaluation",
    description: "Real-versus-generated comparison, scoring outputs, and provider-level analysis.",
    artifactLabel: "Evaluation summaries",
  },
};

export function HomePage() {
  const productsQuery = useApiData(() => api.getProducts(), []);
  const workflowQuery = useApiData(() => api.getWorkflow(), []);

  const products = productsQuery.data?.items ?? [];
  const stages = workflowQuery.data?.stages ?? [];
  const featuredProducts = products
    .map((product) => shortProductNames[product.slug] ?? product.title)
    .slice(0, 3);
  const overviewStats = [
    {
      label: "Selected products",
      value: String(products.length || 0),
      hint: "loaded from processed corpus artifacts",
    },
    {
      label: "Review corpus",
      value: String(products.reduce((sum, item) => sum + item.reviewCount, 0)),
      hint: "cleaned reviews available for downstream analysis",
    },
    {
      label: "Profiles ready",
      value: String(
        products.filter(
          (item) => item.artifacts.profiles.baseline && item.artifacts.profiles.reviewInformed,
        ).length,
      ),
      hint: "products with both baseline and review-informed outputs",
    },
    {
      label: "Evaluation ready",
      value: String(products.filter((item) => item.artifacts.evaluation).length),
      hint: "products with saved comparison summaries",
    },
  ];

  return (
    <>
      <motion.section
        initial={{ opacity: 0, y: 22 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr]"
      >
        <div className="rounded-[2rem] border border-white/70 bg-ink px-8 py-10 text-white shadow-float">
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="text-sm font-semibold uppercase tracking-[0.24em] text-white/70"
          >
            Artifact-backed demo frontend
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="mt-4 max-w-3xl font-display text-5xl font-bold leading-tight lg:text-6xl"
          >
            Product image generation grounded in customer review evidence.
          </motion.h1>
          <p className="mt-5 max-w-2xl text-base text-white/75">
            A full-stack research pipeline linking public product data, structured visual
            understanding, dual-model generation, and comparison analytics.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">Q1-Q4 complete</span>
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">artifact-backed</span>
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">dual-model evaluation</span>
          </div>
          <div className="mt-5 flex flex-wrap gap-3 text-sm text-white/80">
            {featuredProducts.map((name) => (
              <span
                key={name}
                className="rounded-full border border-white/15 bg-white/10 px-4 py-2"
              >
                {name}
              </span>
            ))}
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {overviewStats.map((stat, index) => (
            <StatCard
              key={stat.label}
              {...stat}
              accent={
                [
                  "from-white to-sky-50",
                  "from-white to-orange-50",
                  "from-white to-lime-50",
                  "from-white to-slate-100",
                ][index]
              }
            />
          ))}
        </div>
      </motion.section>

      <AnimatedSection
        eyebrow="Q1 to Q4"
        title="Pipeline status"
        description="Each stage is drawn from saved artifacts and workflow state."
      >
        {workflowQuery.loading ? (
          <LoadingState title="Loading workflow stages" lines={4} />
        ) : (
          <div className="grid gap-5 lg:grid-cols-2">
            {stages.map((stage) => {
              const presentation = stagePresentation[stage.stage] ?? {
                title: stage.label ?? stage.stage,
                description: stage.detail,
                artifactLabel: "Saved artifacts",
              };

              return (
                <StageCard
                  key={stage.stage}
                  title={presentation.title}
                  description={presentation.description}
                  status={stage.status}
                  chips={[
                    `${stage.completedCount}/${stage.totalCount} complete`,
                    presentation.artifactLabel,
                  ]}
                />
              );
            })}
          </div>
        )}
      </AnimatedSection>

      <AnimatedSection
        eyebrow="Rubric focus"
        title="What the demo is optimizing for"
        description="The dashboard mirrors the rubric while reflecting the current repository state."
      >
        <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-4">
          {rubricItems.map((item, index) => (
            <motion.article
              key={item.title}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.07 }}
              whileHover={{ y: -5 }}
              className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
            >
              <ArtifactBadge label={item.title} tone="coral" />
              <h3 className="mt-4 font-display text-2xl font-semibold text-ink">{item.value}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.detail}</p>
            </motion.article>
          ))}
        </div>
      </AnimatedSection>
    </>
  );
}

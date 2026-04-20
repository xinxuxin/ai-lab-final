import { motion } from "framer-motion";
import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { LoadingState } from "../components/LoadingState";
import { StageCard } from "../components/StageCard";
import { StatCard } from "../components/StatCard";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";
import { rubricItems } from "../lib/presentation";

export function HomePage() {
  const productsQuery = useApiData(() => api.getProducts(), []);
  const workflowQuery = useApiData(() => api.getWorkflow(), []);

  const products = productsQuery.data?.items ?? [];
  const stages = workflowQuery.data?.stages ?? [];
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
            Generating product images from customer reviews, with real pipeline artifacts driving every page.
          </motion.h1>
          <p className="mt-5 max-w-2xl text-base text-white/75">
            The dashboard now reads saved outputs from discovery, scraping, corpus building, visual
            profile extraction, image generation, and evaluation. Missing stages stay visible
            instead of being hidden.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">Q1 to Q4 aligned</span>
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">real artifact loading</span>
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">presentation-ready states</span>
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
        title="Four-stage pipeline overview"
        description="Each card is now driven by real artifact-stage progress rather than fixed mock status."
      >
        {workflowQuery.loading ? (
          <LoadingState title="Loading workflow stages" lines={4} />
        ) : (
          <div className="grid gap-5 lg:grid-cols-2">
            {stages.map((stage) => (
              <StageCard
                key={stage.stage}
                title={stage.stage}
                description={stage.detail}
                status={stage.status}
                chips={[
                  `${stage.completedCount}/${stage.totalCount} ready`,
                  stage.artifact,
                ]}
              />
            ))}
          </div>
        )}
      </AnimatedSection>

      <AnimatedSection
        eyebrow="Rubric focus"
        title="What the demo is optimizing for"
        description="The presentation view still mirrors the rubric, but the content now reflects actual repository state."
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

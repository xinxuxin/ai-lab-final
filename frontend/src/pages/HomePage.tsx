import { motion } from "framer-motion";
import { AnimatedSection } from "../components/AnimatedSection";
import { StageCard } from "../components/StageCard";
import { StatCard } from "../components/StatCard";
import { overviewStats, stageCards } from "../data/mockData";

export function HomePage() {
  return (
    <>
      <motion.section
        initial={{ opacity: 0, y: 22 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]"
      >
        <div className="rounded-[2rem] border border-white/70 bg-ink px-8 py-10 text-white shadow-float">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-white/70">
            Full-stack demo shell
          </p>
          <h1 className="mt-4 max-w-2xl font-display text-5xl font-bold leading-tight">
            From public reviews to image prompts, generations, and comparison-ready evidence.
          </h1>
          <p className="mt-5 max-w-2xl text-base text-white/75">
            This dashboard is intentionally staged for the final presentation: every phase produces
            durable artifacts, traceable prompts, and evaluation outputs.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">API-only models</span>
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">Artifact-first workflow</span>
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">Reproducible experiments</span>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {overviewStats.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>
      </motion.section>

      <AnimatedSection
        eyebrow="Pipeline"
        title="Agentic workflow stages"
        description="The skeleton already mirrors the expected report structure: discovery, scraping, retrieval, visual profile extraction, image generation, comparison, and workflow traces."
      >
        <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
          {stageCards.map((stage) => (
            <StageCard key={stage.title} {...stage} />
          ))}
        </div>
      </AnimatedSection>
    </>
  );
}


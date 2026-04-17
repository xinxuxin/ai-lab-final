import { motion } from "framer-motion";
import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { StageCard } from "../components/StageCard";
import { StatCard } from "../components/StatCard";
import { overviewStats, pipelineSteps, rubricItems } from "../mock/projectData";

export function HomePage() {
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
            Presentation demo frontend
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="mt-4 max-w-3xl font-display text-5xl font-bold leading-tight lg:text-6xl"
          >
            Generating product images from customer reviews, with visible evidence at every stage.
          </motion.h1>
          <p className="mt-5 max-w-2xl text-base text-white/75">
            This frontend is already shaped around the assignment structure. It tells the story from
            Q1 product selection to Q4 workflow orchestration, while leaving clean slots for future
            real artifacts, prompts, traces, and evaluation outputs.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">Q1 to Q4 aligned</span>
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">Mock artifact loading</span>
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">Presentation-ready visuals</span>
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
        description="The home page frames the final demo around the assignment questions, so viewers can immediately connect each visual module to the report logic."
      >
        <div className="grid gap-5 lg:grid-cols-2">
          {pipelineSteps.map((stage) => (
            <div key={stage.title} className="space-y-3">
              <StageCard
                title={stage.title}
                description={stage.summary}
                status={stage.status}
                chips={stage.bullets}
              />
            </div>
          ))}
        </div>
      </AnimatedSection>

      <AnimatedSection
        eyebrow="Rubric focus"
        title="What the demo is optimizing for"
        description="These panels mirror the rubric priorities so the presentation UI supports analysis quality, not just visual appeal."
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

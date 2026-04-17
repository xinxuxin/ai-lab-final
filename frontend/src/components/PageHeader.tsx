import { motion } from "framer-motion";
import { ArtifactBadge } from "./ArtifactBadge";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  badges?: string[];
};

export function PageHeader({
  eyebrow,
  title,
  description,
  badges = [],
}: PageHeaderProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="grid gap-5 rounded-[2rem] border border-white/70 bg-ink px-8 py-8 text-white shadow-float lg:grid-cols-[1.4fr_0.6fr]"
    >
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-white/65">{eyebrow}</p>
        <h1 className="mt-3 font-display text-4xl font-bold leading-tight lg:text-5xl">{title}</h1>
        <p className="mt-4 max-w-3xl text-white/75">{description}</p>
      </div>
      <div className="flex flex-wrap content-start gap-2">
        {badges.map((badge) => (
          <ArtifactBadge key={badge} label={badge} tone="sky" />
        ))}
      </div>
    </motion.section>
  );
}


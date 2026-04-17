import { motion } from "framer-motion";
import { PropsWithChildren } from "react";

type AnimatedSectionProps = PropsWithChildren<{
  title: string;
  eyebrow?: string;
  description?: string;
}>;

export function AnimatedSection({
  title,
  eyebrow,
  description,
  children,
}: AnimatedSectionProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="rounded-[2rem] border border-white/70 bg-white/75 p-6 shadow-float backdrop-blur"
    >
      <div className="mb-6">
        {eyebrow ? (
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="font-display text-3xl font-bold text-ink">{title}</h2>
        {description ? <p className="mt-2 max-w-3xl text-slate-600">{description}</p> : null}
      </div>
      {children}
    </motion.section>
  );
}


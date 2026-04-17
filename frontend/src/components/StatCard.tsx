import { motion } from "framer-motion";

type StatCardProps = {
  label: string;
  value: string;
  hint: string;
  accent?: string;
};

export function StatCard({
  label,
  value,
  hint,
  accent = "from-white to-slate-50",
}: StatCardProps) {
  return (
    <motion.article
      whileHover={{ y: -6, scale: 1.01 }}
      transition={{ type: "spring", stiffness: 260, damping: 18 }}
      className={`rounded-[1.75rem] border border-white/70 bg-gradient-to-br p-5 shadow-float ${accent}`}
    >
      <p className="text-sm uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-3 font-display text-4xl font-bold text-ink">{value}</p>
      <p className="mt-3 text-sm text-slate-600">{hint}</p>
    </motion.article>
  );
}

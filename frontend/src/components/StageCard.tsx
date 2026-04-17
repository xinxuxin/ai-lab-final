import { motion } from "framer-motion";
import { ArtifactBadge } from "./ArtifactBadge";

type StageCardProps = {
  title: string;
  description: string;
  status: "Ready" | "Pending" | "Cached" | "Running";
  chips: string[];
};

const statusClasses: Record<StageCardProps["status"], string> = {
  Ready: "bg-lime/70 text-ink",
  Pending: "bg-slate-200 text-slate-700",
  Cached: "bg-glow/70 text-ink",
  Running: "bg-coral/70 text-ink",
};

export function StageCard({ title, description, status, chips }: StageCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -8 }}
      transition={{ type: "spring", stiffness: 220, damping: 18 }}
      className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
    >
      <div className="flex items-start justify-between gap-4">
        <h3 className="font-display text-2xl font-semibold text-ink">{title}</h3>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClasses[status]}`}>
          {status}
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-600">{description}</p>
      <div className="mt-5 flex flex-wrap gap-2">
        {chips.map((chip) => (
          <ArtifactBadge key={chip} label={chip} />
        ))}
      </div>
    </motion.article>
  );
}

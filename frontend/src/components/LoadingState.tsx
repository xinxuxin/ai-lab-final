import { motion } from "framer-motion";

type LoadingStateProps = {
  title?: string;
  lines?: number;
};

export function LoadingState({
  title = "Loading artifact-backed data",
  lines = 3,
}: LoadingStateProps) {
  return (
    <div className="rounded-[1.75rem] border border-white/70 bg-white/80 p-6 shadow-float">
      <p className="font-display text-2xl font-semibold text-ink">{title}</p>
      <div className="mt-5 space-y-3">
        {Array.from({ length: lines }, (_, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0.45 }}
            animate={{ opacity: [0.45, 0.85, 0.45] }}
            transition={{ duration: 1.4, repeat: Number.POSITIVE_INFINITY, delay: index * 0.08 }}
            className="h-4 rounded-full bg-slate-200"
          />
        ))}
      </div>
    </div>
  );
}

import { motion } from "framer-motion";
import { PromptSet } from "../mock/projectData";

type PromptCardProps = {
  prompt: PromptSet;
};

export function PromptCard({ prompt }: PromptCardProps) {
  return (
    <motion.article
      whileHover={{ y: -5 }}
      transition={{ type: "spring", stiffness: 260, damping: 18 }}
      className="rounded-[1.5rem] border border-white/70 bg-white p-5 shadow-float"
    >
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{prompt.label}</p>
      <h3 className="mt-2 font-display text-2xl font-semibold text-ink">{prompt.goal}</h3>
      <p className="mt-4 text-sm leading-6 text-slate-600">{prompt.prompt}</p>
    </motion.article>
  );
}


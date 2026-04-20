import { motion } from "framer-motion";

type PromptCardProps = {
  prompt: {
    prompt_version_id: string;
    strategy: string;
    prompt_source_mode: string;
    prompt_text: string;
    negative_prompt?: string | null;
    notes?: string | null;
  };
};

export function PromptCard({ prompt }: PromptCardProps) {
  return (
    <motion.article
      whileHover={{ y: -5 }}
      transition={{ type: "spring", stiffness: 260, damping: 18 }}
      className="rounded-[1.5rem] border border-white/70 bg-white p-5 shadow-float"
    >
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{prompt.strategy}</p>
      <h3 className="mt-2 font-display text-2xl font-semibold text-ink">
        {prompt.prompt_source_mode}
      </h3>
      <p className="mt-4 text-sm leading-6 text-slate-600">{prompt.prompt_text}</p>
      {prompt.negative_prompt ? (
        <div className="mt-4 rounded-[1.25rem] border border-orange-100 bg-orange-50 p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-orange-700">Negative Prompt</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{prompt.negative_prompt}</p>
        </div>
      ) : null}
    </motion.article>
  );
}

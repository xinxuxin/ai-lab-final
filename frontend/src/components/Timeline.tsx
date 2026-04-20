import { motion } from "framer-motion";

type TimelineProps = {
  items: Array<{
    stage: string;
    detail: string;
    status: "done" | "active" | "pending" | "failed";
  }>;
};

export function Timeline({ items }: TimelineProps) {
  const dotClass = {
    done: "bg-lime",
    active: "bg-coral",
    pending: "bg-slate-300",
    failed: "bg-coral",
  };

  return (
    <div className="space-y-5">
      {items.map((item, index) => (
        <motion.div
          key={item.stage}
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.06 }}
          className="flex gap-4"
        >
          <div className="flex flex-col items-center">
            <motion.div
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ duration: 0.5, delay: index * 0.08 }}
              className={`h-4 w-4 rounded-full ${dotClass[item.status]}`}
            />
            {index < items.length - 1 ? <div className="mt-2 h-full w-px bg-slate-300" /> : null}
          </div>
          <div className="rounded-[1.25rem] border border-white/70 bg-white/80 px-4 py-3 shadow-sm">
            <p className="font-medium text-ink">{item.stage}</p>
            <p className="mt-1 text-sm text-slate-500">{item.detail}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

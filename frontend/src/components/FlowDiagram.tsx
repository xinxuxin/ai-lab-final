import { motion } from "framer-motion";
import { WorkflowNode } from "../mock/projectData";
import { ArtifactBadge } from "./ArtifactBadge";

type FlowDiagramProps = {
  nodes: WorkflowNode[];
};

const statusTone: Record<WorkflowNode["status"], "lime" | "sky" | "coral" | "neutral"> = {
  Ready: "lime",
  Cached: "sky",
  Pending: "neutral",
  Running: "coral",
};

export function FlowDiagram({ nodes }: FlowDiagramProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {nodes.map((node, index) => (
        <motion.div
          key={node.id}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.08 }}
          className="relative rounded-[1.75rem] border border-white/70 bg-white p-5 shadow-float"
        >
          {index < nodes.length - 1 ? (
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ delay: index * 0.12 + 0.1 }}
              className="absolute left-[calc(100%-0.5rem)] top-1/2 hidden h-px w-8 -translate-y-1/2 bg-slate-300 lg:block"
            />
          ) : null}
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{node.role}</p>
              <h3 className="mt-2 font-display text-2xl font-semibold text-ink">{node.title}</h3>
            </div>
            <ArtifactBadge label={node.status} tone={statusTone[node.status]} />
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">{node.detail}</p>
        </motion.div>
      ))}
    </div>
  );
}


import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { FlowDiagram } from "../components/FlowDiagram";
import { LoadingState } from "../components/LoadingState";
import { MissingArtifactState } from "../components/MissingArtifactState";
import { PageHeader } from "../components/PageHeader";
import { Timeline } from "../components/Timeline";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";
import { formatRelativeTimestamp } from "../lib/time";

const toneMap = {
  completed: "lime",
  partial_success: "sky",
  failed: "coral",
} as const;

export function WorkflowPage() {
  const workflowQuery = useApiData(() => api.getWorkflow(), []);
  const stages = workflowQuery.data?.stages ?? [];
  const initialStage = stages[0]?.stage ?? null;
  const [activeStage, setActiveStage] = useState<string | null>(initialStage);

  const syncedActiveStage =
    activeStage && stages.some((stage) => stage.stage === activeStage)
      ? activeStage
      : initialStage;

  const selectedTraces = useMemo(
    () => (workflowQuery.data?.traces ?? []).filter((trace) => trace.stage === syncedActiveStage),
    [syncedActiveStage, workflowQuery.data?.traces],
  );
  const selectedHandoffs = useMemo(
    () =>
      (workflowQuery.data?.handoffs ?? []).filter(
        (handoff) => handoff.fromStage === syncedActiveStage || handoff.toStage === syncedActiveStage,
      ),
    [syncedActiveStage, workflowQuery.data?.handoffs],
  );

  if (workflowQuery.loading && !workflowQuery.data) {
    return <LoadingState title="Loading workflow trace" lines={6} />;
  }

  if (!workflowQuery.data) {
    return (
      <MissingArtifactState
        title="Workflow trace unavailable"
        message="No workflow payload could be loaded from the backend."
      />
    );
  }

  const nodes = stages.map((stage) => ({
    id: stage.stage,
    title: stage.label ?? stage.stage,
    role: stage.agentName ?? "workflow stage",
    detail: stage.detail,
    status: stage.status,
  }));
  const timeline = stages.map((stage) => ({
    stage: stage.label ?? stage.stage,
    detail: `${stage.completedCount}/${stage.totalCount} ready`,
    status: stage.timelineStatus,
  }));

  return (
    <>
      <PageHeader
        eyebrow="Agentic Workflow"
        title="Multi-agent orchestration from Q1 artifacts to Q3 evaluation"
        description="The workflow page now renders a real run trace with typed stage contracts, artifact handoffs, and success or failure states that map directly onto Q1 through Q4."
        badges={[
          workflowQuery.data.latestRun?.scope ?? "artifact-backed",
          workflowQuery.data.latestRun?.status ?? "no-run",
          "inspectable trace",
        ]}
      />

      <AnimatedSection
        title="Latest workflow run"
        description="Each run writes trace, stage-status, and artifact-link files so the final presentation can show exactly how the pipeline moved data between agents."
      >
        {workflowQuery.data.latestRun ? (
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float">
              <div className="flex flex-wrap items-center gap-3">
                <ArtifactBadge label={workflowQuery.data.latestRun.status} tone={toneMap[workflowQuery.data.latestRun.status]} />
                <ArtifactBadge label={workflowQuery.data.latestRun.scope} tone="sky" />
                <ArtifactBadge label={`${workflowQuery.data.latestRun.products.length} products`} tone="neutral" />
              </div>
              <p className="mt-4 text-sm text-slate-600">
                Run ID <span className="font-mono text-ink">{workflowQuery.data.latestRun.runId}</span> was saved{" "}
                {formatRelativeTimestamp(workflowQuery.data.latestRun.createdAt)}.
              </p>
              <p className="mt-4 text-sm leading-6 text-slate-600">
                Products: {workflowQuery.data.latestRun.products.join(", ")}
              </p>
            </div>

            <div className="rounded-[1.75rem] border border-dashed border-slate-300 bg-slate-50 p-6">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Trace Artifacts</p>
              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <p className="font-mono">{workflowQuery.data.latestRun.tracePath}</p>
                <p className="font-mono">{workflowQuery.data.latestRun.stageStatusPath}</p>
                <p className="font-mono">{workflowQuery.data.latestRun.artifactLinksPath}</p>
              </div>
            </div>
          </div>
        ) : (
          <MissingArtifactState
            title="No saved workflow run yet"
            message="Run `python -m cli.main run-workflow --all` to create an inspectable Q4 workflow trace."
          />
        )}
      </AnimatedSection>

      <AnimatedSection
        title="Animated stage diagram"
        description="These agent nodes correspond to Q1 data curation, Q2 retrieval and visual understanding, Q3 prompt composition and image generation, and Q3 or Q4 evaluation analytics."
      >
        {workflowQuery.loading ? (
          <LoadingState title="Loading stage graph" lines={4} />
        ) : (
          <FlowDiagram nodes={nodes} />
        )}
      </AnimatedSection>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <AnimatedSection
          title="Stage timeline"
          description="The timeline shows which agent stages completed, which are only partially available, and where a failure would stop the downstream handoff."
        >
          <Timeline items={timeline} />
        </AnimatedSection>

        <AnimatedSection
          title="Clickable stage inspector"
          description="Select a stage to inspect its trace records and the artifacts it passed to the next agent."
        >
          <div className="flex flex-wrap gap-3">
            {stages.map((stage) => (
              <motion.button
                key={stage.stage}
                whileHover={{ y: -2 }}
                type="button"
                onClick={() => setActiveStage(stage.stage)}
                className={`rounded-full border px-4 py-2 text-sm transition ${
                  syncedActiveStage === stage.stage
                    ? "border-ink bg-ink text-white"
                    : "border-slate-300 bg-white text-slate-700"
                }`}
              >
                {stage.label ?? stage.stage}
              </motion.button>
            ))}
          </div>

          <div className="mt-5 grid gap-4">
            {selectedTraces.length ? (
              selectedTraces.map((trace) => (
                <motion.div
                  key={trace.traceId}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5"
                >
                  <div className="flex flex-wrap items-center gap-3">
                    <ArtifactBadge
                      label={trace.status}
                      tone={trace.status === "completed" ? "lime" : trace.status === "failed" ? "coral" : "sky"}
                    />
                    <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{trace.traceId}</span>
                  </div>
                  <p className="mt-3 text-sm text-slate-600">
                    Started {trace.startedAt ? formatRelativeTimestamp(trace.startedAt) : "n/a"}
                  </p>
                  <div className="mt-4 grid gap-3 lg:grid-cols-2">
                    <div className="rounded-2xl bg-white p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Inputs</p>
                      <pre className="mt-2 overflow-x-auto text-xs text-slate-700">
                        {JSON.stringify(trace.inputs, null, 2)}
                      </pre>
                    </div>
                    <div className="rounded-2xl bg-white p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Outputs</p>
                      <pre className="mt-2 overflow-x-auto text-xs text-slate-700">
                        {JSON.stringify(trace.outputs, null, 2)}
                      </pre>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {trace.notes.map((note) => (
                      <ArtifactBadge key={note} label={note} tone="neutral" />
                    ))}
                  </div>
                </motion.div>
              ))
            ) : (
              <MissingArtifactState
                title="No trace records for this stage"
                message="Run the workflow first or select a different stage."
              />
            )}
          </div>
        </AnimatedSection>
      </div>

      <AnimatedSection
        title="Artifact handoff view"
        description="These handoffs make the workflow visibly agentic by showing how one specialized stage hands durable outputs to the next stage instead of relying on one monolithic prompt."
      >
        <div className="grid gap-4 lg:grid-cols-2">
          {selectedHandoffs.length ? (
            selectedHandoffs.map((handoff) => (
              <motion.div
                key={`${handoff.fromStage}-${handoff.toStage}-${handoff.productSlug ?? "scope"}`}
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="rounded-[1.5rem] border border-white/70 bg-white p-5 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <ArtifactBadge label={handoff.fromStage} tone="sky" />
                  <span className="text-slate-400">→</span>
                  <ArtifactBadge label={handoff.toStage} tone="lime" />
                </div>
                <p className="mt-4 font-medium text-ink">{handoff.label}</p>
                <p className="mt-2 text-sm text-slate-500">
                  {handoff.productSlug ? `Product: ${handoff.productSlug}` : "Run-level handoff"}
                </p>
                <div className="mt-4 space-y-2">
                  {handoff.artifactPaths.map((path) => (
                    <code
                      key={path}
                      className="block overflow-x-auto rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600"
                    >
                      {path}
                    </code>
                  ))}
                </div>
              </motion.div>
            ))
          ) : (
            <MissingArtifactState
              title="No handoffs for this stage"
              message="Select a stage with saved artifact transitions."
            />
          )}
        </div>
      </AnimatedSection>
    </>
  );
}

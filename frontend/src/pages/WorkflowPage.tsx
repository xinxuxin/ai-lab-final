import { AnimatedSection } from "../components/AnimatedSection";
import { FlowDiagram } from "../components/FlowDiagram";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { Timeline } from "../components/Timeline";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";

export function WorkflowPage() {
  const workflowQuery = useApiData(() => api.getWorkflow(), []);

  if (workflowQuery.loading && !workflowQuery.data) {
    return <LoadingState title="Loading workflow trace" lines={5} />;
  }

  const stages = workflowQuery.data?.stages ?? [];
  const nodes = stages.map((stage) => ({
    id: stage.stage,
    title: stage.stage,
    role: "workflow stage",
    detail: stage.detail,
    status: stage.status,
  }));
  const timeline = stages.map((stage) => ({
    stage: stage.stage,
    detail: `${stage.completedCount}/${stage.totalCount} ready`,
    status: stage.timelineStatus,
  }));

  return (
    <>
      <PageHeader
        eyebrow="Agentic Workflow"
        title="Animated multi-agent flow with stage timeline and artifact traces"
        description="This page now reads a real artifact-backed workflow snapshot so viewers can see which stages are complete, partial, or still pending."
        badges={["multi-agent flow", "timeline", "artifact traces"]}
      />

      <AnimatedSection
        title="Multi-stage flow diagram"
        description="Every stage box is now driven by the current artifact state on disk."
      >
        {workflowQuery.loading ? <LoadingState title="Loading stage graph" lines={4} /> : <FlowDiagram nodes={nodes} />}
      </AnimatedSection>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <AnimatedSection
          title="Stage status timeline"
          description="The timeline animates progress based on how many products have completed each stage."
        >
          <Timeline items={timeline} />
        </AnimatedSection>

        <AnimatedSection
          title="Artifact trace view"
          description="These traces describe which durable file each stage is expected to produce."
        >
          <div className="space-y-4">
            {(workflowQuery.data?.traces ?? []).map((trace) => (
              <div
                key={trace.stage}
                className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5"
              >
                <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{trace.stage}</p>
                    <p className="mt-1 font-semibold text-ink">{trace.owner}</p>
                  </div>
                  <code className="rounded-xl bg-white px-3 py-2 text-xs text-slate-600">
                    {trace.artifact}
                  </code>
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-600">{trace.note}</p>
              </div>
            ))}
          </div>
        </AnimatedSection>
      </div>
    </>
  );
}

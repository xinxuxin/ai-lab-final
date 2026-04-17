import { AnimatedSection } from "../components/AnimatedSection";
import { FlowDiagram } from "../components/FlowDiagram";
import { PageHeader } from "../components/PageHeader";
import { Timeline } from "../components/Timeline";
import { workflowNodes, workflowTimeline, workflowTraces } from "../mock/projectData";

export function WorkflowPage() {
  return (
    <>
      <PageHeader
        eyebrow="Agentic Workflow"
        title="Animated multi-agent flow with stage timeline and artifact traces"
        description="This page visually ties the whole repository together. It is designed to demonstrate Q4 by showing agent roles, stage transitions, and the durable artifact outputs each stage is expected to produce."
        badges={["multi-agent flow", "timeline", "artifact traces"]}
      />

      <AnimatedSection
        title="Multi-agent flow diagram"
        description="Each block stands in for a workflow stage owner. Later this page can connect directly to real trace logs."
      >
        <FlowDiagram nodes={workflowNodes} />
      </AnimatedSection>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <AnimatedSection
          title="Stage status timeline"
          description="The timeline exposes progression and waiting points, which helps explain cache-first reruns and stage boundaries."
        >
          <Timeline items={workflowTimeline} />
        </AnimatedSection>

        <AnimatedSection
          title="Artifact trace view"
          description="This panel mirrors the durable files the real workflow will write to disk."
        >
          <div className="space-y-4">
            {workflowTraces.map((trace) => (
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

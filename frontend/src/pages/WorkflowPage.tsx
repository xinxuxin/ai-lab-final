import { AnimatedSection } from "../components/AnimatedSection";
import { Timeline } from "../components/Timeline";
import { workflowTimeline } from "../data/mockData";

export function WorkflowPage() {
  return (
    <AnimatedSection
      eyebrow="Q4"
      title="Workflow stages and traces"
      description="This route is dedicated to the agentic workflow: staged execution, cached artifacts, trace logs, and reproducible reruns with explicit refresh flags."
    >
      <Timeline items={workflowTimeline} />
    </AnimatedSection>
  );
}


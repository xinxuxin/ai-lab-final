export const rubricItems = [
  {
    title: "Experiment Design",
    value: "Controlled stage boundaries",
    detail:
      "The UI exposes stage-specific artifacts so the report can separate product choice, textual grounding, image generation, and comparison analysis.",
  },
  {
    title: "Analytics",
    value: "Artifact-backed evidence",
    detail:
      "Review stats, profile evidence, generation manifests, and evaluation outputs are read from disk rather than mocked in-page logic.",
  },
  {
    title: "Insights",
    value: "Model differences stay visible",
    detail:
      "OpenAI and Stability results are preserved separately so prompt drift, fidelity differences, and failure patterns can be discussed clearly.",
  },
  {
    title: "Scientific Rigor",
    value: "Clear missing-artifact states",
    detail:
      "If a stage has not been run yet, the frontend says so explicitly instead of pretending the pipeline is complete.",
  },
];

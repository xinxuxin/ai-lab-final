export type StageStatus = "Ready" | "Pending" | "Cached";

export const overviewStats = [
  { label: "Target products", value: "3", hint: "exactly three categories" },
  { label: "Image models", value: "2", hint: "OpenAI + Stability" },
  { label: "Images per product", value: "3-5", hint: "with prompt iteration" },
  { label: "Workflow stages", value: "7", hint: "discover to compare" },
];

export const stageCards = [
  {
    title: "Discover Products",
    description: "Find public product candidates, preserve durable seeds, and document selection rationale.",
    status: "Ready" as StageStatus,
    chips: ["Q1", "artifact-first", "respectful crawling"],
  },
  {
    title: "Scrape Reviews",
    description: "Collect public descriptions and reviews once, then reuse cached artifacts downstream by default.",
    status: "Cached" as StageStatus,
    chips: ["Q1", "public-only", "retries"],
  },
  {
    title: "Build Retrieval Corpus",
    description: "Chunk product evidence into reusable retrieval units for analysis prompts and prompt grounding.",
    status: "Pending" as StageStatus,
    chips: ["Q2", "chunking", "RAG-ready"],
  },
  {
    title: "Extract Visual Profile",
    description: "Use prompt-engineered LLM analysis to turn review evidence into image-generation-ready attributes.",
    status: "Pending" as StageStatus,
    chips: ["Q2", "prompting", "OpenAI API"],
  },
  {
    title: "Generate Images",
    description: "Call multiple API-only image providers and track prompt versions, outputs, and failures.",
    status: "Pending" as StageStatus,
    chips: ["Q3", "OpenAI", "Stability"],
  },
  {
    title: "Compare Results",
    description: "Contrast generated images with reference product images and document similarity, differences, and explanations.",
    status: "Pending" as StageStatus,
    chips: ["Q3", "evaluation", "scientific rigor"],
  },
];

export const navLinks = [
  { label: "Overview", href: "/" },
  { label: "Products", href: "/products" },
  { label: "Reviews", href: "/reviews" },
  { label: "Profiles", href: "/profiles" },
  { label: "Generation", href: "/generation" },
  { label: "Comparison", href: "/comparison" },
  { label: "Workflow", href: "/workflow" },
];

export const productCards = [
  {
    title: "Portable Espresso Maker",
    category: "Kitchen",
    popularity: "High",
    note: "Useful for balancing clear functional reviews with lifestyle-oriented visual cues.",
  },
  {
    title: "Mechanical Gaming Keyboard",
    category: "Electronics",
    popularity: "Medium",
    note: "Rich review language around materials, lighting, and layout supports visual profile extraction.",
  },
  {
    title: "Ceramic Skin-Care Organizer",
    category: "Home",
    popularity: "Low",
    note: "Adds a more design-led product with packaging and form-factor comments from niche buyers.",
  },
];

export const reviewBars = [
  { name: "Descriptions", value: 3 },
  { name: "Reviews scraped", value: 126 },
  { name: "Evidence chunks", value: 48 },
  { name: "Prompt variants", value: 9 },
];

export const promptVersions = [
  {
    version: "v1",
    strategy: "direct summarization",
    summary: "Convert description + top reviews into a compact photorealistic product prompt.",
  },
  {
    version: "v2",
    strategy: "retrieved evidence",
    summary: "Ground prompt with review snippets about material, finish, size, and packaging details.",
  },
  {
    version: "v3",
    strategy: "contrastive refinement",
    summary: "Add negative cues and remove lifestyle clutter after comparing with reference images.",
  },
];

export const workflowTimeline = [
  "Candidate discovery and filtering",
  "Public page scrape with artifact cache",
  "Corpus build and chunk manifest",
  "LLM visual profile extraction",
  "Prompt versioning and image generation",
  "Reference comparison and analysis",
  "Report-ready exports and reflection notes",
];

export const imagePlaceholders = [
  { title: "Reference image A", subtitle: "posted product photo" },
  { title: "OpenAI output", subtitle: "prompt v2" },
  { title: "Stability output", subtitle: "prompt v2" },
  { title: "Refined output", subtitle: "prompt v3" },
];


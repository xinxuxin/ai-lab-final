export type StageStatus = "Ready" | "Cached" | "Pending" | "Running";

export type NavItem = {
  label: string;
  href: string;
  short: string;
};

export type ProductCard = {
  id: string;
  title: string;
  category: string;
  popularity: "High" | "Medium" | "Low";
  reviewCount: number;
  categoryFit: string;
  rationale: string;
  visualHook: string;
};

export type ReviewSample = {
  productId: string;
  rating: number;
  title: string;
  body: string;
  tag: string;
};

export type EvidencePanel = {
  title: string;
  snippet: string;
  source: string;
  reason: string;
};

export type AttributeGroup = {
  label: string;
  values: Array<{ name: string; confidence: number }>;
};

export type ConflictItem = {
  attribute: string;
  tension: string;
  interpretation: string;
};

export type PromptSet = {
  id: string;
  label: string;
  goal: string;
  prompt: string;
};

export type GeneratedAsset = {
  title: string;
  subtitle: string;
  status: string;
  tint: string;
};

export type WorkflowNode = {
  id: string;
  title: string;
  role: string;
  detail: string;
  status: StageStatus;
};

export type WorkflowTraceItem = {
  stage: string;
  artifact: string;
  owner: string;
  note: string;
};

export type WorkflowTimelineItem = {
  stage: string;
  detail: string;
  status: "done" | "active" | "pending";
};

export const navLinks: NavItem[] = [
  { label: "Overview", href: "/", short: "Home" },
  { label: "Product Selection", href: "/products", short: "Q1" },
  { label: "Review Explorer", href: "/reviews", short: "Q1-Q2" },
  { label: "Visual Profile", href: "/profiles", short: "Q2" },
  { label: "Image Generation", href: "/generation", short: "Q3" },
  { label: "Comparison Dashboard", href: "/comparison", short: "Q3" },
  { label: "Agentic Workflow", href: "/workflow", short: "Q4" },
];

export const overviewStats = [
  { label: "Selected products", value: "3", hint: "different categories and popularity levels" },
  { label: "Public reviews", value: "126", hint: "artifact-first collection target" },
  { label: "Prompt variants", value: "9", hint: "pilot and final prompts across models" },
  { label: "Evaluation axes", value: "4", hint: "design, analytics, insights, rigor" },
];

export const pipelineSteps = [
  {
    title: "Q1 Product Selection",
    summary:
      "Discover candidate products, justify exactly three selections, and preserve descriptions plus public reviews as durable artifacts.",
    status: "Ready" as StageStatus,
    bullets: ["category spread", "popularity balancing", "artifact manifests"],
  },
  {
    title: "Q2 Text Analysis",
    summary:
      "Chunk saved text, retrieve grounded evidence, and translate reviews into a prompt-ready visual profile using API-only LLM calls.",
    status: "Cached" as StageStatus,
    bullets: ["chunking strategy", "retrieval support", "prompt engineering"],
  },
  {
    title: "Q3 Image Generation",
    summary:
      "Track prompt revisions for OpenAI and Stability outputs, compare pilot and final prompt behavior, and store image artifacts for evaluation.",
    status: "Pending" as StageStatus,
    bullets: ["two API models", "3-5 images each", "prompt iteration"],
  },
  {
    title: "Q4 Agentic Workflow",
    summary:
      "Connect discovery, scraping, retrieval, generation, and evaluation through a traceable multi-stage workflow with reproducible reruns.",
    status: "Pending" as StageStatus,
    bullets: ["workflow traces", "stage caching", "report-ready exports"],
  },
];

export const rubricItems = [
  {
    title: "Experiment Design",
    value: "Clear variable control",
    detail: "The UI separates product choice, retrieval logic, prompt strategy, model choice, and evaluation outputs.",
  },
  {
    title: "Analytics",
    value: "Evidence-first views",
    detail: "Charts, retrieval panels, and score summaries are already designed around saved artifacts rather than ad hoc demos.",
  },
  {
    title: "Insights",
    value: "Model-specific takeaways",
    detail: "Pages reserve space for prompt drift, visual conflicts, and interpretation of differences between providers.",
  },
  {
    title: "Scientific Rigor",
    value: "Reproducible traces",
    detail: "The presentation shell mirrors the final artifact pipeline, making stage boundaries and reruns explicit.",
  },
];

export const selectedProducts: ProductCard[] = [
  {
    id: "espresso-maker",
    title: "Portable Espresso Maker",
    category: "Kitchen",
    popularity: "High",
    reviewCount: 58,
    categoryFit: "Functional appliance with clear material, size, and travel-use cues.",
    rationale:
      "A highly reviewed product gives dense evidence about finish, portability, brewing components, and packaging expectations.",
    visualHook: "Compact matte body, metal accents, travel-ready silhouette.",
  },
  {
    id: "gaming-keyboard",
    title: "Mechanical Gaming Keyboard",
    category: "Electronics",
    popularity: "Medium",
    reviewCount: 41,
    categoryFit: "Tech product with strong comments on lighting, keycap texture, and layout.",
    rationale:
      "Balanced popularity helps compare how review specificity changes when the product is popular enough to be well-described but not saturated.",
    visualHook: "RGB glow, textured keycaps, low-angle desk presentation.",
  },
  {
    id: "skin-organizer",
    title: "Ceramic Skin-Care Organizer",
    category: "Home",
    popularity: "Low",
    reviewCount: 27,
    categoryFit: "Aesthetic home item with nuanced comments on shape, color tone, and countertop context.",
    rationale:
      "Lower-popularity niche products are useful for seeing whether sparse but descriptive reviews still support strong visual reconstruction.",
    visualHook: "Soft ivory ceramic, rounded compartments, boutique packaging cues.",
  },
];

export const productStatHighlights = [
  { label: "Category coverage", value: "Kitchen / Electronics / Home" },
  { label: "Popularity mix", value: "High + Medium + Low" },
  { label: "Review pool", value: "126 public reviews" },
];

export const reviewVolume = [
  { product: "Espresso Maker", reviews: 58, chunks: 18 },
  { product: "Gaming Keyboard", reviews: 41, chunks: 16 },
  { product: "Skin-Care Organizer", reviews: 27, chunks: 14 },
];

export const reviewSamples: ReviewSample[] = [
  {
    productId: "espresso-maker",
    rating: 5,
    title: "Feels premium for travel",
    body: "The matte black shell and silver ring make it look more expensive than it is, and the case feels compact enough for a backpack.",
    tag: "material + portability",
  },
  {
    productId: "gaming-keyboard",
    rating: 4,
    title: "Lighting is bright but not harsh",
    body: "Keys have a slightly textured finish and the underglow is vivid without bleeding into the white legends too much.",
    tag: "lighting + texture",
  },
  {
    productId: "skin-organizer",
    rating: 4,
    title: "Looks softer in person",
    body: "The ceramic is more warm cream than pure white, and the rounded dividers make it look like a boutique vanity piece.",
    tag: "color + form",
  },
];

export const evidencePanels: EvidencePanel[] = [
  {
    title: "Retrieved evidence: material cues",
    snippet: '"matte black shell", "silver ring", and "slightly textured finish" recur across high-rated reviews.',
    source: "review chunks 04, 11, 17",
    reason: "Supports prompt details about surface finish and realism.",
  },
  {
    title: "Retrieved evidence: packaging cues",
    snippet: '"boutique vanity piece" and "travel-ready case" highlight presentation context beyond the core object.',
    source: "review chunks 09, 24",
    reason: "Useful for evaluation when generated images overuse lifestyle scenes.",
  },
  {
    title: "Retrieved evidence: scale and use context",
    snippet: '"compact enough for a backpack" and "low-angle desk presentation" give visual framing hints.',
    source: "review chunks 02, 19",
    reason: "Helps map review language into composition and camera assumptions.",
  },
];

export const ragNotes = [
  "Chunking is designed per review paragraph with metadata for rating, product, and artifact source.",
  "Retrieval is meant to ground appearance claims and reduce hallucinated materials or packaging details.",
  "The explanation panel is intentionally visible in the demo because chunking strategy is part of the assignment's scientific rigor.",
];

export const visualAttributeGroups: AttributeGroup[] = [
  {
    label: "Materials",
    values: [
      { name: "matte polymer shell", confidence: 0.91 },
      { name: "brushed metal accent", confidence: 0.86 },
      { name: "gloss key legends", confidence: 0.77 },
    ],
  },
  {
    label: "Color palette",
    values: [
      { name: "matte black", confidence: 0.93 },
      { name: "warm ivory", confidence: 0.82 },
      { name: "RGB cyan-magenta glow", confidence: 0.74 },
    ],
  },
  {
    label: "Form factors",
    values: [
      { name: "compact cylindrical body", confidence: 0.89 },
      { name: "rounded compartment edges", confidence: 0.83 },
      { name: "low-profile key rows", confidence: 0.8 },
    ],
  },
];

export const conflictingAttributes: ConflictItem[] = [
  {
    attribute: "Color temperature",
    tension: "Some reviews say pure white while others describe warm cream.",
    interpretation: "Prompt should bias toward soft ivory and avoid stark sterile white lighting.",
  },
  {
    attribute: "Metal visibility",
    tension: "Not every reviewer mentions a visible metal ring on the espresso maker.",
    interpretation: "Treat metal as a restrained accent rather than a dominant design element.",
  },
];

export const promptReadyDescription =
  "Photorealistic studio product image of a compact matte-bodied consumer item with restrained metallic accents, soft diffused lighting, clean marketplace composition, subtle packaging context, and materials grounded in customer review evidence. Preserve realistic scale, avoid excessive lifestyle staging, and emphasize finish fidelity over dramatic effects.";

export const generationModels = [
  {
    id: "openai",
    label: "OpenAI",
    subtitle: "Tighter composition and packaging control",
    strengths: ["clean marketplace framing", "controlled prompt following"],
  },
  {
    id: "stability",
    label: "Stability",
    subtitle: "Stronger material texture and stylistic variety",
    strengths: ["surface detail", "variation across iterations"],
  },
];

export const promptVersionsByModel: Record<string, { pilot: PromptSet[]; final: PromptSet[] }> = {
  openai: {
    pilot: [
      {
        id: "oa-pilot-1",
        label: "Pilot v1",
        goal: "Direct visual summary",
        prompt:
          "Create a realistic product photo based on public reviews. Focus on material finish, neutral background, and clear product-centered composition.",
      },
      {
        id: "oa-pilot-2",
        label: "Pilot v2",
        goal: "Evidence-grounded refinement",
        prompt:
          "Use retrieved snippets about matte finish, metallic accent, and compact form to create a marketplace-ready product image with minimal clutter.",
      },
    ],
    final: [
      {
        id: "oa-final-1",
        label: "Final v3",
        goal: "Marketplace fidelity",
        prompt:
          "Photorealistic e-commerce hero shot with accurate finish, review-grounded color tone, restrained packaging context, and realistic camera angle.",
      },
      {
        id: "oa-final-2",
        label: "Final v4",
        goal: "Negative prompt cleanup",
        prompt:
          "Keep object centered, avoid lifestyle scenery, avoid exaggerated reflections, preserve compact scale, and render clean soft-box lighting.",
      },
    ],
  },
  stability: {
    pilot: [
      {
        id: "st-pilot-1",
        label: "Pilot v1",
        goal: "Texture exploration",
        prompt:
          "Render a consumer product based on review attributes, emphasizing material realism and tactile texture in a clean studio layout.",
      },
      {
        id: "st-pilot-2",
        label: "Pilot v2",
        goal: "Composition control",
        prompt:
          "Use retrieved evidence to limit extra objects and keep the product silhouette close to reference listing imagery.",
      },
    ],
    final: [
      {
        id: "st-final-1",
        label: "Final v3",
        goal: "Prompt-constrained realism",
        prompt:
          "Photorealistic product listing image, high material fidelity, soft neutral background, minimal props, accurate color warmth, natural reflection control.",
      },
      {
        id: "st-final-2",
        label: "Final v4",
        goal: "Reference alignment",
        prompt:
          "Prioritize silhouette, material finish, and packaging restraint found in public product photos; reduce stylization and cinematic perspective.",
      },
    ],
  },
};

export const generatedAssetsByModel: Record<string, GeneratedAsset[]> = {
  openai: [
    {
      title: "OpenAI output A",
      subtitle: "final prompt v3",
      status: "best packaging match",
      tint: "from-sky-100 to-white",
    },
    {
      title: "OpenAI output B",
      subtitle: "final prompt v4",
      status: "clean lighting",
      tint: "from-blue-50 to-cyan-100",
    },
    {
      title: "OpenAI output C",
      subtitle: "pilot v2",
      status: "slightly generic",
      tint: "from-slate-100 to-blue-50",
    },
    {
      title: "OpenAI output D",
      subtitle: "reference-aligned",
      status: "final shortlist",
      tint: "from-white to-sky-50",
    },
  ],
  stability: [
    {
      title: "Stability output A",
      subtitle: "final prompt v3",
      status: "best texture detail",
      tint: "from-orange-50 to-white",
    },
    {
      title: "Stability output B",
      subtitle: "final prompt v4",
      status: "strong silhouette",
      tint: "from-rose-50 to-amber-50",
    },
    {
      title: "Stability output C",
      subtitle: "pilot v2",
      status: "more dramatic lighting",
      tint: "from-stone-100 to-amber-50",
    },
    {
      title: "Stability output D",
      subtitle: "texture-heavy variant",
      status: "good material fidelity",
      tint: "from-white to-orange-100",
    },
  ],
};

export const comparisonScores = [
  { metric: "shape fidelity", reference: 94, openai: 89, stability: 84 },
  { metric: "material realism", reference: 96, openai: 85, stability: 91 },
  { metric: "color accuracy", reference: 92, openai: 88, stability: 81 },
  { metric: "marketplace framing", reference: 95, openai: 91, stability: 79 },
];

export const modelComparisonSummary = [
  {
    title: "OpenAI strengths",
    text: "Outputs stay closer to clean listing composition and tend to obey prompt constraints around minimal props and centered framing.",
  },
  {
    title: "Stability strengths",
    text: "Outputs often show more tactile materials and lighting nuance, especially when texture cues are prominent in retrieved evidence.",
  },
  {
    title: "Observed tradeoff",
    text: "One provider preserves e-commerce simplicity better, while the other more strongly captures texture and object personality.",
  },
];

export const comparisonPanels = [
  {
    title: "Reference photo",
    subtitle: "posted marketplace image",
    tint: "from-slate-100 to-slate-200",
  },
  {
    title: "Generated candidate",
    subtitle: "best OpenAI final prompt",
    tint: "from-sky-50 to-white",
  },
  {
    title: "Generated candidate",
    subtitle: "best Stability final prompt",
    tint: "from-orange-50 to-white",
  },
];

export const workflowNodes: WorkflowNode[] = [
  {
    id: "discover",
    title: "Discovery Agent",
    role: "Q1",
    detail: "Collect candidate links and save seeds with rationale hints.",
    status: "Ready",
  },
  {
    id: "scrape",
    title: "Scrape Agent",
    role: "Q1",
    detail: "Pull public descriptions and reviews into durable manifests.",
    status: "Cached",
  },
  {
    id: "retrieve",
    title: "Retrieval Agent",
    role: "Q2",
    detail: "Chunk corpus, rank evidence, and prepare review-grounded snippets.",
    status: "Running",
  },
  {
    id: "profile",
    title: "Profile Agent",
    role: "Q2",
    detail: "Extract structured visual attributes and prompt-ready summaries.",
    status: "Pending",
  },
  {
    id: "generate",
    title: "Generation Agent",
    role: "Q3",
    detail: "Call image APIs, track prompt versions, and store image outputs.",
    status: "Pending",
  },
  {
    id: "evaluate",
    title: "Evaluation Agent",
    role: "Q3-Q4",
    detail: "Compare outputs, score fidelity, and write explanation artifacts.",
    status: "Pending",
  },
];

export const workflowTimeline: WorkflowTimelineItem[] = [
  { stage: "Discovery manifest", detail: "18 candidate links saved", status: "done" },
  { stage: "Selection shortlist", detail: "3 products locked for report", status: "done" },
  { stage: "Scrape cache", detail: "descriptions and reviews persisted", status: "done" },
  { stage: "Retrieval corpus", detail: "chunk manifest being assembled", status: "active" },
  { stage: "Profile extraction", detail: "awaiting LLM output", status: "pending" },
  { stage: "Image generation", detail: "queued after prompt freeze", status: "pending" },
];

export const workflowTraces: WorkflowTraceItem[] = [
  {
    stage: "discover-products",
    artifact: "artifacts/raw/discovery_candidates.json",
    owner: "Discovery Agent",
    note: "Stores candidate URLs, category tags, and popularity hints.",
  },
  {
    stage: "scrape-all",
    artifact: "artifacts/raw/reviews_manifest.json",
    owner: "Scrape Agent",
    note: "Contains saved public product descriptions and review records.",
  },
  {
    stage: "build-corpus",
    artifact: "artifacts/processed/retrieval_chunks.json",
    owner: "Retrieval Agent",
    note: "Links every chunk to product, source review, and chunk metadata.",
  },
  {
    stage: "extract-visual-profile",
    artifact: "artifacts/processed/visual_profiles.json",
    owner: "Profile Agent",
    note: "Will hold structured attributes, confidence, and prompt-ready text.",
  },
];

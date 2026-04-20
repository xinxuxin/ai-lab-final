export type ApiStatus = "ok" | "partial" | "missing_artifact";

export type ProductSummary = {
  slug: string;
  title: string;
  category: string;
  selectedCategory: string;
  marketplace: string;
  sourceUrl: string;
  reviewCount: number;
  visibleReviewCount: number | null;
  imageCount: number;
  descriptionCharCount: number;
  rationale?: string | null;
  popularityHint?: string | null;
  primaryImageUrl?: string | null;
  freshness: Record<string, string | null>;
  artifacts: {
    processed: boolean;
    profiles: { baseline: boolean; reviewInformed: boolean };
    generation: { openai: boolean; stability: boolean };
    evaluation: boolean;
  };
};

export type ProductsResponse = {
  status: ApiStatus;
  generatedAt?: string | null;
  message?: string;
  items: ProductSummary[];
};

export type ProductDetailResponse = {
  status: ApiStatus;
  product: {
    slug: string;
    title: string;
    category: string;
    selectedCategory: string;
    marketplace: string;
    sourceUrl: string;
    reviewCount: number;
    visibleReviewCount: number | null;
    imageCount: number;
    rating?: number | null;
    popularityHint?: string | null;
    rationale?: string | null;
    descriptionText: string;
    specBullets: string[];
    referenceImages: Array<{ filename: string; url: string }>;
    freshness?: string | null;
  };
};

export type ReviewStatsResponse = {
  status: ApiStatus;
  message?: string;
  productSlug: string;
  stats?: Record<string, number | null>;
  samples?: Array<Record<string, unknown>>;
  evidenceSnippets?: Array<{
    mode: string;
    aspect: string;
    snippet: string;
    score?: number;
  }>;
  freshness?: Record<string, string | null>;
};

export type ProfileModePayload = {
  status: "available" | "missing_artifact";
  updatedAt?: string | null;
  message?: string;
  profile?: {
    product_name: string;
    category: string;
    high_confidence_visual_attributes: Array<{
      attribute: string;
      rationale: string;
      evidence_snippets: string[];
    }>;
    low_confidence_or_conflicting_attributes: Array<{
      attribute: string;
      rationale: string;
      evidence_snippets: string[];
    }>;
    common_mismatches_between_expectation_and_reality: Array<{
      mismatch: string;
      evidence_snippets: string[];
    }>;
    prompt_ready_description: string;
    negative_constraints: string[];
  };
};

export type ProfileResponse = {
  status: ApiStatus;
  productSlug: string;
  modes: Record<string, ProfileModePayload>;
  retrievalEvidence: Record<string, unknown>;
  llmTrace: Record<string, unknown>;
  missingArtifacts: string[];
  freshness: Record<string, string | null>;
};

export type GenerationResponse = {
  status: ApiStatus;
  productSlug: string;
  referenceImages: Array<{ filename: string; url: string }>;
  models: Record<
    string,
    | {
        status: "missing_artifact";
        message: string;
      }
    | {
        status: "available";
        manifest: {
          provider: string;
          model_name: string;
          pilot_generation: { prompt_source_mode: string };
          final_generation: { prompt_source_mode: string };
        };
        promptVersions: {
          versions: Array<{
            prompt_version_id: string;
            strategy: "pilot" | "final";
            prompt_source_mode: string;
            prompt_text: string;
            negative_prompt?: string | null;
            negative_constraints?: string[];
            notes?: string | null;
          }>;
        };
        pilotImages: Array<{ filename: string; url: string; width: number; height: number }>;
        finalImages: Array<{ filename: string; url: string; width: number; height: number }>;
        updatedAt?: string | null;
      }
  >;
  missingArtifacts: string[];
  freshness: Record<string, string | null>;
};

export type EvaluationResponse = {
  status: ApiStatus;
  productSlug: string;
  message?: string;
  summary?: {
    status: string;
    product_name: string;
    category: string;
    reference_image_count: number;
    comparison_panel_count: number;
    available_models: string[];
    missing_models: string[];
    vision_assisted_status: string;
    aggregate_scores: Record<string, Record<string, number>>;
    summary_text: string;
  };
  comparisonPanels?: Array<{
    panel_id: string;
    provider: string;
    model_name: string;
    referenceImageUrl: string;
    generatedImageUrl: string;
    prompt_source_mode: string;
  }>;
  visionAssisted?: Record<string, unknown>;
  humanScoreSheetUrl?: string;
  freshness?: string | null;
};

export type WorkflowResponse = {
  status: ApiStatus;
  latestRun: null | {
    runId: string;
    createdAt: string;
    scope: "single" | "all";
    status: "completed" | "partial_success" | "failed";
    products: string[];
    tracePath: string;
    stageStatusPath: string;
    artifactLinksPath: string;
  };
  stages: Array<{
    stage: string;
    label?: string;
    agentName?: string;
    status: "Ready" | "Cached" | "Pending" | "Running" | "Failed";
    timelineStatus: "done" | "active" | "pending" | "failed";
    artifact: string;
    completedCount: number;
    totalCount: number;
    detail: string;
    products?: string[];
  }>;
  traces: Array<{
    traceId: string;
    stage: string;
    status: string;
    startedAt: string | null;
    finishedAt: string | null;
    inputs: Record<string, string>;
    outputs: Record<string, string>;
    notes: string[];
  }>;
  handoffs: Array<{
    fromStage: string;
    toStage: string;
    label: string;
    productSlug: string | null;
    artifactPaths: string[];
  }>;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export function resolveApiUrl(path: string) {
  return API_BASE ? `${API_BASE}${path}` : path;
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(resolveApiUrl(path));
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export const api = {
  getProducts: () => fetchJson<ProductsResponse>("/api/products"),
  getProduct: (slug: string) => fetchJson<ProductDetailResponse>(`/api/products/${slug}`),
  getReviews: (slug: string) => fetchJson<ReviewStatsResponse>(`/api/reviews/${slug}/stats`),
  getProfiles: (slug: string) => fetchJson<ProfileResponse>(`/api/profiles/${slug}`),
  getGeneration: (slug: string) => fetchJson<GenerationResponse>(`/api/generation/${slug}`),
  getEvaluation: (slug: string) => fetchJson<EvaluationResponse>(`/api/evaluation/${slug}`),
  getWorkflow: () => fetchJson<WorkflowResponse>("/api/workflow/latest"),
};

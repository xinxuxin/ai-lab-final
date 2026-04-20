import { useEffect, useMemo, useState } from "react";
import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { FreshnessBadge } from "../components/FreshnessBadge";
import { ImageGrid } from "../components/ImageGrid";
import { LoadingState } from "../components/LoadingState";
import { MissingArtifactState } from "../components/MissingArtifactState";
import { PageHeader } from "../components/PageHeader";
import { ProductSelector } from "../components/ProductSelector";
import { PromptCard } from "../components/PromptCard";
import { useApiData } from "../hooks/useApiData";
import { api } from "../lib/api";

export function GenerationPage() {
  const productsQuery = useApiData(() => api.getProducts(), []);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState("openai");
  const [promptTab, setPromptTab] = useState<"pilot" | "final">("pilot");

  useEffect(() => {
    if (!selectedSlug && productsQuery.data?.items?.length) {
      const preferred =
        productsQuery.data.items.find(
          (item) => item.artifacts.generation.openai || item.artifacts.generation.stability,
        ) ?? productsQuery.data.items[0];
      setSelectedSlug(preferred.slug);
    }
  }, [productsQuery.data, selectedSlug]);

  const generationQuery = useApiData(
    () => api.getGeneration(selectedSlug ?? ""),
    [selectedSlug],
    { enabled: Boolean(selectedSlug) },
  );

  const activeModel = useMemo(() => {
    const model = generationQuery.data?.models?.[selectedModel];
    if (!model || model.status === "missing_artifact") {
      return null;
    }
    return model;
  }, [generationQuery.data, selectedModel]);

  const activePrompts = useMemo(() => {
    if (!activeModel) {
      return [];
    }
    return activeModel.promptVersions.versions.filter((item) => item.strategy === promptTab);
  }, [activeModel, promptTab]);

  const activeImages = useMemo(() => {
    if (!activeModel) {
      return [];
    }
    return (promptTab === "pilot" ? activeModel.pilotImages : activeModel.finalImages).map((image) => ({
      title: image.filename,
      subtitle: `${image.width} × ${image.height}`,
      imageUrl: image.url,
      status: selectedModel,
    }));
  }, [activeModel, promptTab, selectedModel]);

  return (
    <>
      <PageHeader
        eyebrow="Image Generation"
        title="Model switching, prompt evolution, and candidate output grids"
        description="The generation page now loads real prompt histories and generated image artifacts when they exist, and it shows clear missing-artifact states when they do not."
        badges={["OpenAI / Stability", "pilot vs final", "artifact-backed"]}
      />

      <ProductSelector
        products={productsQuery.data?.items ?? []}
        selectedSlug={selectedSlug}
        onSelect={setSelectedSlug}
      />

      <AnimatedSection
        title="Model switcher"
        description="Switch between providers to compare saved prompt versions and generated outputs."
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-3">
            {["openai", "stability"].map((model) => (
              <button
                key={model}
                type="button"
                onClick={() => setSelectedModel(model)}
                className={`rounded-full px-5 py-3 text-sm font-semibold transition ${
                  selectedModel === model
                    ? "bg-ink text-white shadow-float"
                    : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
                }`}
              >
                {model}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            <FreshnessBadge value={activeModel?.updatedAt} label="generation" />
            <ArtifactBadge
              label={activeModel ? "artifacts available" : "artifacts missing"}
              tone={activeModel ? "lime" : "coral"}
            />
          </div>
        </div>
      </AnimatedSection>

      {generationQuery.loading ? (
        <LoadingState title="Loading generation artifacts" lines={5} />
      ) : !activeModel ? (
        <MissingArtifactState
          title="Generation artifacts missing"
          message={
            generationQuery.data?.models?.[selectedModel]?.status === "missing_artifact"
              ? (generationQuery.data.models[selectedModel] as { message: string }).message
              : "This product does not have saved generation artifacts for the selected model."
          }
          details={generationQuery.data?.missingArtifacts}
        />
      ) : (
        <>
          <AnimatedSection
            title="Prompt version history"
            description="Prompt versions are loaded from saved prompt artifacts, with pilot and final tabs."
          >
            <div className="mb-5 flex gap-3">
              {(["pilot", "final"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setPromptTab(tab)}
                  className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                    promptTab === tab ? "bg-coral text-ink" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {tab === "pilot" ? "Pilot prompts" : "Final prompts"}
                </button>
              ))}
            </div>
            <div className="grid gap-5 lg:grid-cols-2">
              {activePrompts.map((prompt) => (
                <PromptCard key={prompt.prompt_version_id} prompt={prompt} />
              ))}
            </div>
          </AnimatedSection>

          <AnimatedSection
            title="Reference product images"
            description="Reference marketplace images are shown alongside generated outputs for presentation context."
          >
            <ImageGrid
              items={(generationQuery.data?.referenceImages ?? []).slice(0, 4).map((image) => ({
                title: image.filename,
                subtitle: "reference image",
                imageUrl: image.url,
                status: "reference",
              }))}
            />
          </AnimatedSection>

          <AnimatedSection
            title="Generated image grid"
            description="Pilot and final outputs stay separated so prompt iteration remains visible."
          >
            <ImageGrid items={activeImages} />
          </AnimatedSection>
        </>
      )}
    </>
  );
}

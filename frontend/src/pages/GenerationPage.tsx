import { useState } from "react";
import { AnimatedSection } from "../components/AnimatedSection";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { ImageGrid } from "../components/ImageGrid";
import { PageHeader } from "../components/PageHeader";
import { PromptCard } from "../components/PromptCard";
import {
  generatedAssetsByModel,
  generationModels,
  promptVersionsByModel,
} from "../mock/projectData";

export function GenerationPage() {
  const [selectedModel, setSelectedModel] = useState("openai");
  const [promptTab, setPromptTab] = useState<"pilot" | "final">("pilot");

  const activeModel = generationModels.find((model) => model.id === selectedModel) ?? generationModels[0];
  const activePrompts = promptVersionsByModel[selectedModel][promptTab];
  const activeImages = generatedAssetsByModel[selectedModel];

  return (
    <>
      <PageHeader
        eyebrow="Image Generation"
        title="Model switching, prompt evolution, and candidate output grids"
        description="This page is built for Q3 presentations. It already supports provider switching, pilot-versus-final prompt tabs, and image grids that can later be replaced by saved outputs."
        badges={["OpenAI / Stability", "pilot vs final", "image grid"]}
      />

      <AnimatedSection
        title="Model switcher"
        description="Switch between providers to compare prompt philosophy and output tendencies."
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-3">
            {generationModels.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => setSelectedModel(model.id)}
                className={`rounded-full px-5 py-3 text-sm font-semibold transition ${
                  selectedModel === model.id
                    ? "bg-ink text-white shadow-float"
                    : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
                }`}
              >
                {model.label}
              </button>
            ))}
          </div>
          <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-5 py-4">
            <p className="font-semibold text-ink">{activeModel.label}</p>
            <p className="mt-1 text-sm text-slate-500">{activeModel.subtitle}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {activeModel.strengths.map((item) => (
                <ArtifactBadge key={item} label={item} tone="sky" />
              ))}
            </div>
          </div>
        </div>
      </AnimatedSection>

      <AnimatedSection
        title="Prompt versions"
        description="Pilot prompts test direction. Final prompts tighten realism, composition, and comparison readiness."
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
            <PromptCard key={prompt.id} prompt={prompt} />
          ))}
        </div>
      </AnimatedSection>

      <AnimatedSection
        title="Final generated image grid"
        description="These placeholders already mirror the final gallery layout for side-by-side provider comparison."
      >
        <ImageGrid items={activeImages} />
      </AnimatedSection>
    </>
  );
}

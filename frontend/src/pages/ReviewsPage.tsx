import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AnimatedSection } from "../components/AnimatedSection";
import { PageHeader } from "../components/PageHeader";
import { ArtifactBadge } from "../components/ArtifactBadge";
import { evidencePanels, ragNotes, reviewSamples, reviewVolume } from "../mock/projectData";

export function ReviewsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Review Explorer"
        title="Review evidence, chunking, and retrieval in one presentation view"
        description="This page is built to explain both the data scale and the retrieval logic. It shows review counts, example review snippets, retrieved evidence panels, and a dedicated chunking and RAG explanation area."
        badges={["review chart", "retrieved evidence", "chunking notes"]}
      />

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <AnimatedSection
          title="Review count and chunk coverage"
          description="Two bars per product show the relationship between raw reviews and downstream chunk units."
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={reviewVolume}>
                <CartesianGrid strokeDasharray="4 4" stroke="#d7dfed" />
                <XAxis dataKey="product" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip />
                <Bar dataKey="reviews" fill="#8ec5ff" radius={[10, 10, 0, 0]} />
                <Bar dataKey="chunks" fill="#ff8a72" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </AnimatedSection>

        <AnimatedSection
          title="Chunking and RAG explanation"
          description="The demo makes the retrieval strategy visible because it is part of the methodology, not just backend plumbing."
        >
          <div className="space-y-4">
            {ragNotes.map((note) => (
              <div
                key={note}
                className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-600"
              >
                {note}
              </div>
            ))}
          </div>
        </AnimatedSection>
      </div>

      <AnimatedSection
        title="Sample review cards"
        description="Short review examples let the audience see the kind of language the pipeline is actually converting into visual evidence."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          {reviewSamples.map((review) => (
            <article
              key={review.title}
              className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
            >
              <div className="flex items-center justify-between gap-3">
                <ArtifactBadge label={review.tag} tone="coral" />
                <p className="text-sm font-medium text-slate-500">{review.rating}.0 / 5</p>
              </div>
              <h3 className="mt-4 font-display text-2xl font-semibold text-ink">{review.title}</h3>
              <p className="mt-4 text-sm leading-6 text-slate-600">{review.body}</p>
            </article>
          ))}
        </div>
      </AnimatedSection>

      <AnimatedSection
        title="Retrieved evidence panels"
        description="These panels mimic the exact evidence view we will eventually populate from saved retrieval outputs."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          {evidencePanels.map((panel) => (
            <article
              key={panel.title}
              className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
            >
              <ArtifactBadge label={panel.source} tone="sky" />
              <h3 className="mt-4 font-display text-2xl font-semibold text-ink">{panel.title}</h3>
              <p className="mt-4 text-sm italic leading-6 text-slate-700">{panel.snippet}</p>
              <p className="mt-4 text-sm leading-6 text-slate-600">{panel.reason}</p>
            </article>
          ))}
        </div>
      </AnimatedSection>
    </>
  );
}

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
import { reviewBars } from "../data/mockData";

export function ReviewsPage() {
  return (
    <AnimatedSection
      eyebrow="Q1 to Q2"
      title="Scraped review stats"
      description="The final version will bind to saved manifests and show crawl results, source coverage, chunk counts, and retrieval evidence quality."
    >
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float">
          <p className="mb-4 font-display text-2xl font-semibold text-ink">Corpus snapshot</p>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={reviewBars}>
                <CartesianGrid strokeDasharray="4 4" stroke="#d7dfed" />
                <XAxis dataKey="name" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip />
                <Bar dataKey="value" fill="#8ec5ff" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float">
          <p className="font-display text-2xl font-semibold text-ink">Evidence retrieval panel</p>
          <div className="mt-5 space-y-4">
            {[
              "Chunking strategy and review-level provenance",
              "Top evidence snippets used to describe materials and appearance",
              "Saved manifests for reproducibility and downstream prompt inspection",
            ].map((item) => (
              <div
                key={item}
                className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600"
              >
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </AnimatedSection>
  );
}


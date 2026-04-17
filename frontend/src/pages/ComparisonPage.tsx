import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AnimatedSection } from "../components/AnimatedSection";
import { ImageGrid } from "../components/ImageGrid";
import { PageHeader } from "../components/PageHeader";
import {
  comparisonPanels,
  comparisonScores,
  modelComparisonSummary,
} from "../mock/projectData";

export function ComparisonPage() {
  return (
    <>
      <PageHeader
        eyebrow="Comparison Dashboard"
        title="Reference versus generated image evaluation"
        description="This page compares real product images with generated outputs, then summarizes scoring patterns and model-specific strengths in a form that can support the final discussion section."
        badges={["reference vs generated", "score charts", "model summary"]}
      />

      <AnimatedSection
        title="Panel comparison"
        description="The grid is already sized for real listing images and generated candidates."
      >
        <ImageGrid items={comparisonPanels} />
      </AnimatedSection>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <AnimatedSection
          title="Score comparison"
          description="Bar charts make it easy to explain which provider is closer to reference across core evaluation metrics."
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonScores}>
                <CartesianGrid strokeDasharray="4 4" stroke="#d7dfed" />
                <XAxis dataKey="metric" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip />
                <Legend />
                <Bar dataKey="openai" fill="#8ec5ff" radius={[10, 10, 0, 0]} />
                <Bar dataKey="stability" fill="#ff8a72" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </AnimatedSection>

        <AnimatedSection
          title="Radar view"
          description="The radar visualization is useful for presentation because the tradeoffs become legible at a glance."
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={comparisonScores}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis domain={[0, 100]} />
                <Radar dataKey="openai" stroke="#0ea5e9" fill="#8ec5ff" fillOpacity={0.35} />
                <Radar dataKey="stability" stroke="#f97316" fill="#ff8a72" fillOpacity={0.22} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </AnimatedSection>
      </div>

      <AnimatedSection
        title="Model comparison summary"
        description="These summary blocks reserve space for the narrative interpretation of observed differences."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          {modelComparisonSummary.map((item) => (
            <article
              key={item.title}
              className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
            >
              <h3 className="font-display text-2xl font-semibold text-ink">{item.title}</h3>
              <p className="mt-4 text-sm leading-6 text-slate-600">{item.text}</p>
            </article>
          ))}
        </div>
      </AnimatedSection>
    </>
  );
}

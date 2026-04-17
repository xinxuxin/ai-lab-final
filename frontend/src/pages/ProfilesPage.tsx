import { AnimatedSection } from "../components/AnimatedSection";
import { ConfidenceChip } from "../components/ConfidenceChip";
import { PageHeader } from "../components/PageHeader";
import {
  conflictingAttributes,
  promptReadyDescription,
  visualAttributeGroups,
} from "../mock/projectData";

export function ProfilesPage() {
  return (
    <>
      <PageHeader
        eyebrow="Visual Profile"
        title="Structured attributes extracted from review evidence"
        description="This page is designed for Q2. It presents extracted visual attributes, confidence chips, conflicts, and the final prompt-ready description that will feed image generation."
        badges={["structured attributes", "confidence", "prompt-ready output"]}
      />

      <AnimatedSection
        title="Structured extracted attributes"
        description="Attribute groups are organized to feel like real downstream artifacts rather than ad hoc notes."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          {visualAttributeGroups.map((group) => (
            <article
              key={group.label}
              className="rounded-[1.75rem] border border-white/70 bg-white p-6 shadow-float"
            >
              <h3 className="font-display text-2xl font-semibold text-ink">{group.label}</h3>
              <div className="mt-5 space-y-4">
                {group.values.map((item) => (
                  <div
                    key={item.name}
                    className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4"
                  >
                    <p className="font-medium text-ink">{item.name}</p>
                    <div className="mt-3">
                      <ConfidenceChip label="evidence confidence" value={item.confidence} />
                    </div>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </AnimatedSection>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <AnimatedSection
          title="Conflicting attributes"
          description="Visible disagreement between reviews is a feature, not a bug. The page highlights those tensions before prompt freezing."
        >
          <div className="space-y-4">
            {conflictingAttributes.map((item) => (
              <div
                key={item.attribute}
                className="rounded-[1.5rem] border border-orange-100 bg-orange-50 p-5"
              >
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-orange-700">
                  {item.attribute}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-700">{item.tension}</p>
                <p className="mt-3 text-sm leading-6 text-slate-600">{item.interpretation}</p>
              </div>
            ))}
          </div>
        </AnimatedSection>

        <AnimatedSection
          title="Prompt-ready description"
          description="This box intentionally looks like a final output artifact that can be copied into generation workflows later."
        >
          <div className="rounded-[1.75rem] border border-slate-200 bg-slate-950 p-6 text-slate-100 shadow-inner">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">final prompt-ready profile</p>
            <p className="mt-4 text-sm leading-7 text-slate-200">{promptReadyDescription}</p>
          </div>
        </AnimatedSection>
      </div>
    </>
  );
}

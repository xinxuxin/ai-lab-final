import { ArtifactBadge } from "./ArtifactBadge";
import { formatFreshness } from "../lib/time";

type FreshnessBadgeProps = {
  value?: string | null;
  label?: string;
};

export function FreshnessBadge({ value, label = "updated" }: FreshnessBadgeProps) {
  const tone = value ? "lime" : "neutral";
  return <ArtifactBadge label={`${label}: ${formatFreshness(value)}`} tone={tone} />;
}

export function formatFreshness(value?: string | null) {
  if (!value) {
    return "missing";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "unknown";
  }
  return date.toLocaleString();
}

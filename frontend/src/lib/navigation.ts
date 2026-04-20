export type NavItem = {
  label: string;
  href: string;
  short: string;
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

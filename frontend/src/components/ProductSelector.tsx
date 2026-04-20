import { ProductSummary } from "../lib/api";

type ProductSelectorProps = {
  products: ProductSummary[];
  selectedSlug: string | null;
  onSelect: (slug: string) => void;
};

export function ProductSelector({
  products,
  selectedSlug,
  onSelect,
}: ProductSelectorProps) {
  return (
    <div className="flex flex-wrap gap-3">
      {products.map((product) => (
        <button
          key={product.slug}
          type="button"
          onClick={() => onSelect(product.slug)}
          className={`rounded-full px-5 py-3 text-sm font-semibold transition ${
            selectedSlug === product.slug
              ? "bg-ink text-white shadow-float"
              : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
          }`}
        >
          {product.title}
        </button>
      ))}
    </div>
  );
}

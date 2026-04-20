import { motion } from "framer-motion";
import { ArtifactBadge } from "./ArtifactBadge";

type ImageGridItem = {
  title: string;
  subtitle: string;
  imageUrl?: string | null;
  alt?: string;
  status?: string;
  tint?: string;
};

type ImageGridProps = {
  items: ImageGridItem[];
};

export function ImageGrid({ items }: ImageGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item, index) => (
        <motion.div
          key={item.title}
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.08 }}
          whileHover={{ y: -6 }}
          className={`overflow-hidden rounded-[1.5rem] border border-white/70 bg-gradient-to-br p-4 shadow-float ${item.tint ?? "from-slate-100 to-slate-200"}`}
        >
          {item.imageUrl ? (
            <div className="flex h-48 items-center justify-center overflow-hidden rounded-[1.25rem] bg-white/80">
              <img
                src={item.imageUrl}
                alt={item.alt ?? item.title}
                className="h-full w-full object-contain"
              />
            </div>
          ) : (
            <div className="flex h-48 items-center justify-center rounded-[1.25rem] border border-dashed border-slate-300 bg-white/60">
              <span className="font-display text-lg text-slate-400">Artifact Missing</span>
            </div>
          )}
          <div className="mt-4 flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-ink">{item.title}</p>
              <p className="text-sm text-slate-500">{item.subtitle}</p>
            </div>
            {item.status ? <ArtifactBadge label={item.status} tone="sky" /> : null}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

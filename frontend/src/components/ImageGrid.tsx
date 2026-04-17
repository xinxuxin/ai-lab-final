import { motion } from "framer-motion";

type ImageGridItem = {
  title: string;
  subtitle: string;
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
          className="overflow-hidden rounded-[1.5rem] border border-white/70 bg-gradient-to-br from-slate-100 to-slate-200 p-4 shadow-float"
        >
          <div className="flex h-48 items-center justify-center rounded-[1.25rem] border border-dashed border-slate-300 bg-white/60">
            <span className="font-display text-lg text-slate-400">Image Placeholder</span>
          </div>
          <p className="mt-4 font-semibold text-ink">{item.title}</p>
          <p className="text-sm text-slate-500">{item.subtitle}</p>
        </motion.div>
      ))}
    </div>
  );
}


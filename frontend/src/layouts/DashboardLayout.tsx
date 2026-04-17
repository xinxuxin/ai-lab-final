import { AnimatePresence, motion } from "framer-motion";
import { PropsWithChildren } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { navLinks } from "../mock/projectData";

export function DashboardLayout({ children }: PropsWithChildren) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-sand bg-mesh text-ink">
      <header className="sticky top-0 z-30 border-b border-white/60 bg-sand/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="font-display text-xl font-bold">CMU Final Project</p>
            <p className="text-sm text-slate-500">Generating Product Image from Customer Reviews</p>
          </div>
          <nav className="hidden gap-2 lg:flex">
            {navLinks.map((link) => (
              <NavLink
                key={link.href}
                to={link.href}
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 text-sm font-medium transition ${
                    isActive ? "bg-ink text-white" : "text-slate-600 hover:bg-white/70"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
          <nav className="-mx-2 flex gap-2 overflow-x-auto px-2 pb-1 lg:hidden">
            {navLinks.map((link) => (
              <NavLink
                key={link.href}
                to={link.href}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition ${
                    isActive ? "bg-ink text-white" : "bg-white/70 text-slate-600"
                  }`
                }
              >
                {link.short}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.32 }}
            className="flex flex-col gap-8"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

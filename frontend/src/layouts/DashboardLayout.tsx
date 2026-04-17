import { PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";
import { navLinks } from "../data/mockData";

export function DashboardLayout({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-sand bg-mesh text-ink">
      <header className="sticky top-0 z-30 border-b border-white/60 bg-sand/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
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
        </div>
      </header>
      <main className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10">{children}</main>
    </div>
  );
}


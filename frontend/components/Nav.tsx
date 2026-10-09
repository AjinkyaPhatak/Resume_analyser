"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/analyse", label: "Analyse" },
  { href: "/research", label: "Research" },
  { href: "/auth", label: "Sign in" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-page/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="whitespace-nowrap font-semibold tracking-tight text-ink">
          Resume <span className="text-accent">Analyser</span>
        </Link>
        <div className="flex items-center gap-1 text-sm">
          {LINKS.map((l) => {
            const active = path === l.href || (l.href !== "/" && path.startsWith(l.href));
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`whitespace-nowrap rounded-md px-2 py-1.5 transition sm:px-3 ${active ? "bg-accent-wash text-accent-ink font-medium" : "text-ink-2 hover:bg-surface-2 hover:text-ink"}`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}

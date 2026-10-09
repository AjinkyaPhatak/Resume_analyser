import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";

import Nav from "@/components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Resume Analyser",
  description:
    "Match a resume to a job description by skills, not by who wrote it: entity-level matching with a counterfactual fairness check.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-page text-ink antialiased">
        <Nav />
        {children}
        <footer className="mt-24 border-t border-line">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-6 text-xs text-muted">
            <span>
              Research prototype. Scores support, and never replace, a human reading the resume.
            </span>
            <Link href="/research" className="hover:text-ink">
              How it works and how it was tested →
            </Link>
          </div>
        </footer>
      </body>
    </html>
  );
}

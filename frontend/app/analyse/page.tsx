"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import api, { errorMessage } from "@/lib/api";
import type { StoredAnalysis } from "@/lib/types";

type Status = { ready: boolean; loading: boolean; error: string | null } | null;

function MatcherStatus({ status, reachable }: { status: Status; reachable: boolean }) {
  if (!reachable)
    return (
      <p className="rounded-lg border border-line bg-surface px-4 py-3 text-sm text-critical">
        ✕ Can&apos;t reach the API at port 8000. Start the backend (see the README).
      </p>
    );
  if (!status) return null;
  if (status.error)
    return (
      <p className="rounded-lg border border-line bg-surface px-4 py-3 text-sm text-critical">✕ Matcher unavailable: {status.error}</p>
    );
  if (!status.ready)
    return (
      <p className="rounded-lg border border-line bg-surface px-4 py-3 text-sm text-warning-ink">
        ◌ Loading the models (skill tagger, ESCO, JobBERT-v2). This takes about a minute after the backend starts.
      </p>
    );
  return <p className="rounded-lg border border-line bg-surface px-4 py-3 text-sm text-good">✓ Matcher ready</p>;
}

export default function AnalysePage() {
  const router = useRouter();
  const [mode, setMode] = useState<"pdf" | "text">("pdf");
  const [filename, setFilename] = useState<string | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState<Status>(null);
  const [reachable, setReachable] = useState(true);

  useEffect(() => {
    let stop = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const r = await api.get("/analysis/status");
        if (stop) return;
        setReachable(true);
        setStatus(r.data);
        if (!r.data.ready && !r.data.error) timer = setTimeout(poll, 3000);
      } catch {
        if (stop) return;
        setReachable(false);
        timer = setTimeout(poll, 5000);
      }
    };
    poll();
    return () => {
      stop = true;
      clearTimeout(timer);
    };
  }, []);

  const onFile = async (file: File | undefined) => {
    if (!file) return;
    setError("");
    setParsing(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await api.post("/resume/parse", form, { headers: { "Content-Type": "multipart/form-data" } });
      setFilename(r.data.filename);
      setResumeText(r.data.text);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setParsing(false);
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!resumeText.trim()) return setError(mode === "pdf" ? "Upload a resume PDF first." : "Paste the resume text.");
    if (!jdText.trim()) return setError("Paste a job description.");
    setLoading(true);
    try {
      const [match, bias] = await Promise.all([
        api.post("/analysis/match", { resume_text: resumeText, jd_text: jdText }),
        api.post("/analysis/bias", { text: jdText }),
      ]);
      const stored: StoredAnalysis = { filename, resume_text: resumeText, jd_text: jdText, match: match.data, bias: bias.data };
      sessionStorage.setItem("analysis", JSON.stringify(stored));
      router.push("/results");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const tab = (m: "pdf" | "text", label: string) => (
    <button
      type="button"
      onClick={() => setMode(m)}
      className={`rounded-md px-3 py-1.5 text-sm transition ${mode === m ? "bg-surface text-ink shadow-sm" : "text-ink-2 hover:text-ink"}`}
    >
      {label}
    </button>
  );

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-bold tracking-tight">Analyse a resume</h1>
      <p className="mt-2 text-ink-2">
        You&apos;ll get a skill-level match score, the requirements that limit it, and an optional fairness check that
        shows how the score reacts to swapped names, pronouns and wording. Nothing you enter is stored.
      </p>
      <div className="mt-6">
        <MatcherStatus status={status} reachable={reachable} />
      </div>

      <form onSubmit={onSubmit} className="mt-8 space-y-8">
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="font-medium">Resume</label>
            <div className="flex gap-1 rounded-lg bg-surface-2 p-1">
              {tab("pdf", "Upload PDF")}
              {tab("text", "Paste text")}
            </div>
          </div>
          {mode === "pdf" && (
            <label
              htmlFor="file-upload"
              className="block cursor-pointer rounded-xl border-2 border-dashed border-line bg-surface p-6 text-center transition hover:border-accent"
            >
              <input id="file-upload" type="file" accept=".pdf" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} />
              {parsing ? (
                <span className="text-ink-2">Reading the PDF…</span>
              ) : filename ? (
                <span className="font-medium text-accent-ink">{filename} · click to replace</span>
              ) : (
                <span className="text-ink-2">Click to choose a PDF</span>
              )}
            </label>
          )}
          {(mode === "text" || resumeText) && (
            <div>
              {mode === "pdf" && <p className="mb-1 text-xs text-muted">Extracted text. Check it, and fix anything the PDF reader got wrong.</p>}
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                rows={mode === "text" ? 10 : 6}
                placeholder="Paste the resume text here…"
                className="w-full resize-y rounded-xl border border-line bg-surface px-4 py-3 text-sm placeholder:text-muted focus:border-accent focus:outline-none"
              />
            </div>
          )}
        </section>

        <section className="space-y-3">
          <label className="font-medium" htmlFor="jd">
            Job description
          </label>
          <textarea
            id="jd"
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            rows={10}
            placeholder="Paste the full job posting here…"
            className="w-full resize-y rounded-xl border border-line bg-surface px-4 py-3 text-sm placeholder:text-muted focus:border-accent focus:outline-none"
          />
        </section>

        {error && <p className="text-sm text-critical">✕ {error}</p>}

        <button
          type="submit"
          disabled={loading || parsing || !status?.ready}
          className="w-full rounded-xl bg-accent py-3 font-medium text-white transition hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Analysing…" : "Analyse"}
        </button>
      </form>
    </main>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function AnalysePage() {
  const router = useRouter();
  const [jdText, setJdText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!file) return setError("Please upload a resume PDF");
    if (!jdText.trim()) return setError("Please paste a job description");

    setLoading(true);

    try {
      // step 1 — upload resume and get text + id
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await api.post("/resume/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const { resume_id } = uploadRes.data;

      // get full resume text
      const resumeRes = await api.get(`/resume/${resume_id}`);
      const fullText = resumeRes.data.raw_text;

      // step 2 — semantic match with full text
      const matchRes = await api.post("/analysis/match", {
        resume_text: fullText,
        jd_text: jdText,
      });

      // step 3 — bias detection on JD
      const biasRes = await api.post("/analysis/bias", {
        text: jdText,
      });

      // store results and navigate
      localStorage.setItem(
        "results",
        JSON.stringify({
          resume_id,
          match: matchRes.data,
          bias: biasRes.data,
        }),
      );

      router.push("/results");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white px-4 py-12">
      <div className="max-w-2xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold">Analyse Your Resume</h1>
          <p className="text-gray-400 mt-1">
            Upload your resume and paste a job description to get your match
            score and bias report.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Resume Upload */}
          <div className="space-y-2">
            <label className="text-sm text-gray-400">Resume (PDF only)</label>
            <div className="border-2 border-dashed border-gray-700 rounded-xl p-6 text-center hover:border-blue-500 transition">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                {file ? (
                  <p className="text-blue-400 font-medium">{file.name}</p>
                ) : (
                  <p className="text-gray-500">
                    Click to upload or drag and drop your PDF
                  </p>
                )}
              </label>
            </div>
          </div>

          {/* JD Input */}
          <div className="space-y-2">
            <label className="text-sm text-gray-400">Job Description</label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={8}
              placeholder="Paste the full job description here..."
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 rounded-xl font-medium transition"
          >
            {loading ? "Analysing..." : "Analyse Now"}
          </button>
        </form>
      </div>
    </main>
  );
}

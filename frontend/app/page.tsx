import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center px-4">
      <div className="max-w-2xl text-center space-y-6">
        <h1 className="text-5xl font-bold tracking-tight">
          Resume <span className="text-blue-500">Analyser</span>
        </h1>
        <p className="text-gray-400 text-lg">
          Go beyond keywords. Match your resume to any job description
          semantically, and detect bias in your language — powered by BERT.
        </p>
        <div className="flex gap-4 justify-center pt-4">
          <Link
            href="/analyse"
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition"
          >
            Analyse My Resume
          </Link>
          <Link
            href="/auth"
            className="border border-gray-600 hover:border-gray-400 text-gray-300 px-6 py-3 rounded-lg font-medium transition"
          >
            Sign In
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-4 pt-8 text-left">
          <div className="bg-gray-900 rounded-xl p-5 space-y-2">
            <h3 className="font-semibold text-blue-400">Semantic Matching</h3>
            <p className="text-gray-400 text-sm">
              Understands that "built ML pipelines" and "machine learning
              engineering" mean the same thing — keyword tools don't.
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 space-y-2">
            <h3 className="font-semibold text-blue-400">Bias Detection</h3>
            <p className="text-gray-400 text-sm">
              Flags gendered and demographically coded language in resumes and
              job descriptions based on peer-reviewed research.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

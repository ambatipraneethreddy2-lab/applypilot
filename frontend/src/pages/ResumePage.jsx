import { useEffect, useState } from "react";
import { api } from "../api";

export default function ResumePage() {
  const [resume, setResume] = useState(undefined);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/resumes/latest").then(setResume).catch((e) => setError(e.message));
  }, []);

  async function upload(e) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      setResume(await api("/api/resumes", { method: "POST", form }));
      setFile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="font-display text-2xl">Your resume</h1>
        <p className="text-muted text-sm mt-1">
          Every job is scored against your latest resume. Uploading a new one re-scores your recent jobs.
        </p>
      </div>

      <form onSubmit={upload} className="card p-5 flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm file:mr-3 file:rounded-lg file:border file:border-line file:bg-white file:px-3 file:py-1.5 file:text-sm"
        />
        <button className="btn-primary ml-auto" disabled={!file || loading}>
          {loading ? "Reading resume…" : resume ? "Upload new version" : "Upload"}
        </button>
        {error && <p className="text-sm text-warn w-full">{error}</p>}
      </form>

      {resume && (
        <section className="card p-5">
          <div className="flex justify-between text-sm">
            <span className="font-medium">{resume.filename}</span>
            <span className="text-muted">{new Date(resume.created_at).toLocaleDateString()}</span>
          </div>
          <h2 className="text-xs font-semibold text-muted uppercase tracking-wide mt-4 mb-2">
            Skills found ({resume.skills.length})
          </h2>
          <div className="flex flex-wrap gap-1.5">
            {resume.skills.map((s) => (
              <span key={s} className="chip bg-accent-soft text-accent">{s}</span>
            ))}
          </div>
          <h2 className="text-xs font-semibold text-muted uppercase tracking-wide mt-5 mb-2">Text preview</h2>
          <pre className="text-xs whitespace-pre-wrap bg-paper rounded-lg p-3 max-h-60 overflow-auto">
            {resume.text_preview}…
          </pre>
        </section>
      )}
      {resume === null && <p className="text-sm text-muted">No resume uploaded yet.</p>}
    </div>
  );
}

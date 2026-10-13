import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, STATUSES } from "../api";
import ScoreBadge from "../components/ScoreBadge";

export default function Board() {
  const [jobs, setJobs] = useState(null);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(null);

  useEffect(() => {
    api("/api/jobs").then(setJobs).catch((e) => setError(e.message));
  }, []);

  // Optimistic update: move the card instantly, roll back if the server says no.
  async function move(jobId, status) {
    const before = jobs;
    setJobs(jobs.map((j) => (j.id === jobId ? { ...j, status } : j)));
    try {
      const updated = await api(`/api/jobs/${jobId}`, { method: "PATCH", body: { status } });
      setJobs((cur) => cur.map((j) => (j.id === jobId ? updated : j)));
    } catch (e) {
      setJobs(before);
      setError(e.message);
    }
  }

  if (jobs === null) return <p className="text-muted">{error || "Loading your board…"}</p>;

  if (jobs.length === 0)
    return (
      <div className="card p-10 text-center max-w-lg mx-auto mt-10">
        <h2 className="font-display text-2xl">No jobs yet</h2>
        <p className="text-muted mt-2">Upload your resume, then paste your first job posting to see your match score.</p>
        <div className="mt-6 flex gap-3 justify-center">
          <Link to="/resume" className="btn-ghost">Upload resume</Link>
          <Link to="/add" className="btn-primary">Add a job</Link>
        </div>
      </div>
    );

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-display text-2xl">Your applications</h1>
        <Link to="/add" className="btn-primary">+ Add job</Link>
      </div>
      {error && <p className="text-sm text-warn mb-3">{error}</p>}

      <div className="grid grid-flow-col auto-cols-[minmax(240px,1fr)] gap-3 overflow-x-auto pb-4">
        {STATUSES.map((col) => {
          const items = jobs.filter((j) => j.status === col.key);
          return (
            <section
              key={col.key}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(col.key);
              }}
              onDragLeave={() => setDragOver(null)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(null);
                const id = Number(e.dataTransfer.getData("text/plain"));
                if (id) move(id, col.key);
              }}
              className={`rounded-xl p-2 min-h-[60vh] transition ${
                dragOver === col.key ? "bg-accent-soft" : "bg-line/40"
              }`}
            >
              <h2 className="px-2 py-1 text-sm font-semibold text-muted flex justify-between">
                {col.label}
                <span className="tabular-nums">{items.length}</span>
              </h2>
              <div className="space-y-2 mt-1">
                {items.map((job) => (
                  <article
                    key={job.id}
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData("text/plain", String(job.id))}
                    className="card p-3 cursor-grab active:cursor-grabbing hover:shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <Link to={`/jobs/${job.id}`} className="font-medium leading-snug hover:text-accent">
                        {job.title || "Untitled role"}
                      </Link>
                      <ScoreBadge score={job.match_score} />
                    </div>
                    <p className="text-sm text-muted mt-0.5">{job.company || "Unknown company"}</p>
                    {job.location && <p className="text-xs text-muted mt-1">{job.location}</p>}
                    {/* Dropdown fallback: drag-and-drop doesn't work on phones */}
                    <select
                      aria-label="Move to"
                      className="mt-2 w-full text-xs border border-line rounded-md px-2 py-1 bg-paper"
                      value={job.status}
                      onChange={(e) => move(job.id, e.target.value)}
                    >
                      {STATUSES.map((s) => (
                        <option key={s.key} value={s.key}>{s.label}</option>
                      ))}
                    </select>
                  </article>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

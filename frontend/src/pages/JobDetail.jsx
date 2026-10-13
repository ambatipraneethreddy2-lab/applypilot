import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, STATUSES } from "../api";
import ScoreBadge from "../components/ScoreBadge";

function Chips({ items, tone }) {
  if (!items?.length) return <p className="text-sm text-muted">None</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((s) => (
        <span key={s} className={`chip ${tone}`}>{s}</span>
      ))}
    </div>
  );
}

function CopyButton({ text }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      className="text-xs text-accent font-medium"
      onClick={() => {
        navigator.clipboard.writeText(text);
        setDone(true);
        setTimeout(() => setDone(false), 1500);
      }}
    >
      {done ? "Copied" : "Copy"}
    </button>
  );
}

export default function JobDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api(`/api/jobs/${id}`)
      .then((j) => {
        setJob(j);
        setNotes(j.notes);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  async function run(label, fn) {
    setBusy(label);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  }

  const patch = (body) => run("save", async () => setJob(await api(`/api/jobs/${id}`, { method: "PATCH", body })));

  if (!job) return <p className="text-muted">{error || "Loading…"}</p>;

  return (
    <div className="max-w-5xl mx-auto">
      <Link to="/" className="text-sm text-muted hover:text-ink">← Back to board</Link>

      <header className="mt-3 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl">{job.title || "Untitled role"}</h1>
          <p className="text-muted mt-1">
            {[job.company, job.location, job.salary].filter(Boolean).join(" · ") || "No details extracted"}
          </p>
          {job.url && (
            <a href={job.url} target="_blank" rel="noreferrer" className="text-sm text-accent">View original posting ↗</a>
          )}
        </div>
        <select className="input w-auto" value={job.status} onChange={(e) => patch({ status: e.target.value })}>
          {STATUSES.map((s) => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
        </select>
      </header>

      {error && <p className="text-sm text-warn mt-3">{error}</p>}

      <div className="grid md:grid-cols-3 gap-4 mt-6">
        {/* Match */}
        <section className="card p-5 md:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Resume match</h2>
            <button
              className="btn-ghost text-xs py-1"
              disabled={!!busy}
              onClick={() => run("rematch", async () => setJob(await api(`/api/jobs/${id}/rematch`, { method: "POST" })))}
            >
              {busy === "rematch" ? "Scoring…" : "Re-score"}
            </button>
          </div>
          {job.match_score == null ? (
            <p className="text-sm text-muted mt-3">
              No score yet. <Link to="/resume" className="text-accent">Upload your resume</Link> and it will score
              automatically.
            </p>
          ) : (
            <>
              <div className="flex items-center gap-4 mt-4">
                <ScoreBadge score={job.match_score} large />
                <p className="text-sm leading-relaxed">{job.match_summary}</p>
              </div>
              <div className="grid sm:grid-cols-2 gap-4 mt-5">
                <div>
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">You have</h3>
                  <Chips items={job.matched_skills} tone="bg-accent-soft text-accent" />
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Missing</h3>
                  <Chips items={job.missing_skills} tone="bg-warn-soft text-warn" />
                </div>
              </div>
            </>
          )}
        </section>

        {/* Notes */}
        <section className="card p-5">
          <h2 className="font-semibold">Notes</h2>
          <textarea
            className="input mt-3 min-h-[140px]"
            placeholder="Recruiter name, referral, follow-up date…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <button className="btn-ghost mt-2 text-xs py-1" disabled={notes === job.notes || !!busy} onClick={() => patch({ notes })}>
            Save notes
          </button>
        </section>

        {/* Tailoring */}
        <section className="card p-5 md:col-span-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Tailored for this job</h2>
            <button
              className="btn-primary text-xs py-1.5"
              disabled={!!busy}
              onClick={() => run("tailor", async () => setJob(await api(`/api/jobs/${id}/tailor`, { method: "POST" })))}
            >
              {busy === "tailor" ? "Writing…" : job.tailored_bullets.length ? "Regenerate" : "Generate bullets + cover letter"}
            </button>
          </div>
          {job.tailored_bullets.length > 0 && (
            <div className="grid md:grid-cols-2 gap-6 mt-4">
              <div>
                <div className="flex justify-between mb-2">
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Resume bullets</h3>
                  <CopyButton text={job.tailored_bullets.map((b) => `• ${b}`).join("\n")} />
                </div>
                <ul className="space-y-2 text-sm list-disc pl-5">
                  {job.tailored_bullets.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Cover letter</h3>
                  <CopyButton text={job.cover_letter} />
                </div>
                <p className="text-sm whitespace-pre-line leading-relaxed">{job.cover_letter}</p>
              </div>
            </div>
          )}
          <p className="text-xs text-muted mt-4">Always review AI text before sending. It only uses what's in your resume.</p>
        </section>

        <section className="card p-5 md:col-span-3">
          <h2 className="font-semibold">Extracted requirements</h2>
          <div className="grid sm:grid-cols-2 gap-4 mt-3">
            <div>
              <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Required</h3>
              <Chips items={job.required_skills} tone="bg-paper border border-line" />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Nice to have</h3>
              <Chips items={job.nice_to_have_skills} tone="bg-paper border border-line" />
            </div>
          </div>
          {job.deadline && <p className="text-sm mt-4">Deadline: {job.deadline}</p>}
        </section>
      </div>

      <button
        className="text-sm text-warn mt-6"
        onClick={() =>
          confirm("Delete this job?") &&
          run("delete", async () => {
            await api(`/api/jobs/${id}`, { method: "DELETE" });
            navigate("/");
          })
        }
      >
        Delete job
      </button>
    </div>
  );
}

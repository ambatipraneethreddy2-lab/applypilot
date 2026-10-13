import { useEffect, useState } from "react";
import { api, STATUSES } from "../api";

function Stat({ label, value, hint }) {
  return (
    <div className="card p-4">
      <p className="text-xs text-muted uppercase tracking-wide font-semibold">{label}</p>
      <p className="font-display text-3xl mt-1 tabular-nums">{value}</p>
      {hint && <p className="text-xs text-muted mt-1">{hint}</p>}
    </div>
  );
}

export default function Dashboard() {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/dashboard").then(setD).catch((e) => setError(e.message));
  }, []);

  if (!d) return <p className="text-muted">{error || "Loading…"}</p>;
  const maxStatus = Math.max(1, ...Object.values(d.by_status));
  const maxSkill = Math.max(1, ...d.top_missing_skills.map((s) => s.count));

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl">Insights</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Jobs tracked" value={d.total} />
        <Stat label="Applied this week" value={d.applied_this_week} />
        <Stat label="Interview rate" value={`${d.interview_rate}%`} hint="of applications reaching interview" />
        <Stat label="Avg match" value={d.average_match_score == null ? "—" : `${d.average_match_score}%`} />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <section className="card p-5">
          <h2 className="font-semibold">Pipeline</h2>
          <div className="space-y-2 mt-4">
            {STATUSES.map((s) => (
              <div key={s.key} className="flex items-center gap-3 text-sm">
                <span className="w-20 text-muted">{s.label}</span>
                <div className="flex-1 bg-paper rounded h-5">
                  <div className="bg-accent h-5 rounded" style={{ width: `${(d.by_status[s.key] / maxStatus) * 100}%` }} />
                </div>
                <span className="w-6 text-right tabular-nums">{d.by_status[s.key]}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="card p-5">
          <h2 className="font-semibold">Skills to learn next</h2>
          <p className="text-xs text-muted mt-1">How many of your saved jobs list each skill you're missing.</p>
          {d.top_missing_skills.length === 0 ? (
            <p className="text-sm text-muted mt-4">Add jobs and a resume to see your gaps.</p>
          ) : (
            <div className="space-y-2 mt-4">
              {d.top_missing_skills.map((s) => (
                <div key={s.skill} className="flex items-center gap-3 text-sm">
                  <span className="w-28 truncate">{s.skill}</span>
                  <div className="flex-1 bg-paper rounded h-5">
                    <div className="bg-warn h-5 rounded" style={{ width: `${(s.count / maxSkill) * 100}%` }} />
                  </div>
                  <span className="w-16 text-right tabular-nums text-muted whitespace-nowrap">{s.count} jobs</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

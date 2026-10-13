import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function AddJob() {
  const [rawText, setRawText] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const job = await api("/api/jobs", { method: "POST", body: { raw_text: rawText, url } });
      navigate(`/jobs/${job.id}`);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="max-w-3xl mx-auto space-y-4">
      <div>
        <h1 className="font-display text-2xl">Add a job</h1>
        <p className="text-muted text-sm mt-1">
          Copy the full job description from LinkedIn, Indeed or the company site and paste it below. The AI pulls out
          the details and scores it against your resume.
        </p>
      </div>
      <input
        className="input"
        type="url"
        placeholder="Job link (optional)"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      <textarea
        className="input min-h-[340px] font-mono text-[13px]"
        placeholder="Paste the job description here…"
        required
        minLength={50}
        value={rawText}
        onChange={(e) => setRawText(e.target.value)}
      />
      {error && <p className="text-sm text-warn">{error}</p>}
      <button className="btn-primary" disabled={loading || rawText.trim().length < 50}>
        {loading ? "Analyzing posting…" : "Analyze & save"}
      </button>
    </form>
  );
}

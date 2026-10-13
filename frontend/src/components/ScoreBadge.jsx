export function scoreTone(score) {
  if (score == null) return "bg-line text-muted";
  if (score >= 70) return "bg-accent-soft text-accent";
  if (score >= 45) return "bg-amber-100 text-amber-800";
  return "bg-warn-soft text-warn";
}

export default function ScoreBadge({ score, large = false }) {
  const text = score == null ? "—" : Math.round(score);
  return (
    <span
      title="Match score: 70% skill coverage + 30% overall similarity"
      className={`${scoreTone(score)} rounded-full font-semibold tabular-nums ${
        large ? "text-2xl px-4 py-1.5" : "text-xs px-2 py-0.5"
      }`}
    >
      {text}
      {score != null && <span className={large ? "text-sm" : "text-[10px]"}>%</span>}
    </span>
  );
}

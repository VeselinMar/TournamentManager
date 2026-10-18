import type { TimelineMatch } from "../types/match";

/** Score line with penalties / extra time, e.g. "1 : 1 (4–3 pens)". */
export function resultText(match: TimelineMatch): string {
  const score = `${match.home_score} : ${match.away_score}`;
  if (match.decided_by === "penalties") {
    return `${score} (${match.home_penalties}–${match.away_penalties} pens)`;
  }
  if (match.decided_by === "extra_time") {
    return `${score} (a.e.t.)`;
  }
  return score;
}

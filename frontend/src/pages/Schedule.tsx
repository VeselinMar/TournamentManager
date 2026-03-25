import { useEffect, useState } from "react";
import apiClient from "../api/client";
import type { Match } from "../types/match";

interface ScheduleProps {
  slug: string;
}

export default function Schedule({ slug }: ScheduleProps) {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMatches = async () => {
    try {
      const res = await apiClient.get<Match[]>(`/tournaments/${slug}/schedule/`);
      setMatches(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Poll every 10 minutes if tournament is not finished
  useEffect(() => {
    fetchMatches();
    const interval = setInterval(fetchMatches, 600000);
    return () => clearInterval(interval);
  }, [slug]);

  if (loading) return <div>Loading schedule…</div>;
  if (!matches.length) return <div>No matches scheduled yet.</div>;

  return (
    <div>
      <h2>Schedule</h2>
      {matches.map((m) => (
        <div key={m.id} style={{ marginBottom: "0.5rem" }}>
          <strong>{new Date(m.start_time).toLocaleTimeString()}</strong>:{" "}
          {m.home_team} vs {m.away_team} @ {m.field} —{" "}
          {m.is_finished
            ? `${m.home_score} : ${m.away_score}`
            : "Not finished"}
        </div>
      ))}
    </div>
  );
}
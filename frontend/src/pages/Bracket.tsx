import { useCallback, useEffect, useState } from "react";
import apiClient from "../api/client";
import type { BracketResponse, TimelineMatch } from "../types/match";
import { TeamName } from "../components/MatchResult";
import { resultText } from "../utils/match";

interface Props {
  slug: string;
}

const REFRESH_MS = 60000;

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function MatchCard({ match }: { match: TimelineMatch }) {
  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #d6e2d6",
        borderLeft: match.is_finished ? "3px solid #2e7d32" : "3px solid #f9a825",
        borderRadius: 8,
        padding: "8px 10px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        fontSize: "0.92rem",
      }}
    >
      <div style={{ fontSize: "0.7rem", color: "#5b6b5b", marginBottom: 4 }}>
        {formatTime(match.start_time)} · {match.field}
      </div>
      <div>
        <TeamName
          name={match.home_team}
          placeholder={match.home_placeholder}
          isWinner={match.winner === match.home_team}
        />
      </div>
      <div>
        <TeamName
          name={match.away_team}
          placeholder={match.away_placeholder}
          isWinner={match.winner === match.away_team}
        />
      </div>
      {match.is_finished && (
        <div style={{ marginTop: 4, fontWeight: 800, color: "#1b5e20" }}>
          {resultText(match)}
        </div>
      )}
    </div>
  );
}

export default function Bracket({ slug }: Props) {
  const [data, setData] = useState<BracketResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchBracket = useCallback(async () => {
    try {
      const res = await apiClient.get<BracketResponse>(`/tournaments/${slug}/bracket/`);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    const first = window.setTimeout(fetchBracket, 0);
    const interval = window.setInterval(fetchBracket, REFRESH_MS);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(interval);
    };
  }, [fetchBracket]);

  if (loading) return <div style={{ padding: 12 }}>Loading bracket...</div>;
  if (!data || data.rounds.length === 0)
    return <div style={{ padding: 12 }}>No knockout stage for this tournament</div>;

  return (
    <div
      style={{
        display: "flex",
        gap: 16,
        overflowX: "auto",
        padding: "4px 2px 12px",
        scrollSnapType: "x mandatory",
      }}
    >
      {data.rounds.map((round) => (
        <section
          key={`${round.label}-${round.round}`}
          style={{
            flex: "0 0 min(260px, 85vw)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-around",
            gap: 12,
            scrollSnapAlign: "start",
          }}
        >
          <h2
            style={{
              margin: 0,
              background: "#1f3a1f",
              color: "#fff",
              borderRadius: 8,
              padding: "8px 10px",
              fontSize: "0.95rem",
              textAlign: "center",
            }}
          >
            {round.label}
          </h2>
          {round.matches.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </section>
      ))}
    </div>
  );
}

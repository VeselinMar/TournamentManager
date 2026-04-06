import { useEffect, useState } from "react";
import apiClient from "../api/client";
import type { LeaderboardResponse } from "../types/leaderboard";

interface Props {
  slug: string;
}

export default function Leaderboard({ slug }: Props) {
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchLeaderboard = async () => {
    try {
      const res = await apiClient.get<LeaderboardResponse>(
        `/tournaments/${slug}/leaderboard/`
      );
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, 80000);
    return () => clearInterval(interval);
  }, [slug]);

  if (loading) return <div style={{ padding: 12 }}>Loading leaderboard...</div>;
  if (!data) return <div style={{ padding: 12 }}>No leaderboard available</div>;

  return (
    <div
      style={{
        width: "100%",
        border: "2px solid #556b2f",
        borderRadius: 8,
        boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
        overflow: "hidden",
        background: "#7da87d",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          background: "#556b2f",
          color: "#fff",
          padding: "10px",
          fontWeight: 700,
          textAlign: "center",
          letterSpacing: 1,
        }}
      >
        Leaderboard
      </div>

      {/* TABLE CONTAINER (mobile scroll) */}
      <div
        style={{
          overflowX: "auto",
        }}
      >
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "clamp(0.85rem, 1vw, 1rem)",
            background: "#8fbc8f",
            color: "#1b1b1b",
            minWidth: 500,
          }}
        >
          <thead>
            <tr>
              {["#", "Team", "Pts", "W", "D", "L", "GF", "GA", "GD"].map(
                (h, i) => (
                  <th
                    key={i}
                    style={{
                      position: "sticky",
                      top: 0,
                      zIndex: 10,
                      backgroundColor: "#556b2f",
                      color: "#fff",
                      padding: "8px",
                      textAlign: "center",
                      border: "2px solid #a5d6a7",
                      fontWeight: 700,
                      textTransform: "uppercase",
                    }}
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>

          <tbody>
            {data.standings.map((team, idx) => {
              const isTop = idx === 0;
              const isPodium = idx < 3;

              return (
                <tr
                  key={team.team_name}
                  style={{
                    background: isTop
                      ? "linear-gradient(to right, #ffd70033, transparent)"
                      : idx % 2 === 0
                      ? "rgba(255,255,255,0.05)"
                      : "rgba(0,0,0,0.03)",
                    transition: "background 0.2s ease",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor =
                      "rgba(255,255,255,0.12)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor = "")
                  }
                >
                  {/* Rank */}
                  <td
                    style={{
                      textAlign: "center",
                      fontWeight: 800,
                      padding: "6px",
                      color: isPodium ? "#1b3a00" : "#333",
                    }}
                  >
                    {idx + 1}
                  </td>

                  {/* Team */}
                  <td
                    style={{
                      padding: "6px",
                      fontWeight: 600,
                    }}
                  >
                    {team.team_name}
                  </td>

                  {/* Points */}
                  <td
                    style={{
                      textAlign: "center",
                      fontWeight: 900,
                      fontSize: "1.05em",
                    }}
                  >
                    {team.points}
                  </td>

                  {/* Stats */}
                  {[
                    team.wins,
                    team.draws,
                    team.losses,
                    team.goals_for,
                    team.goals_against,
                  ].map((val, i) => (
                    <td
                      key={i}
                      style={{
                        textAlign: "center",
                        padding: "6px",
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {val}
                    </td>
                  ))}

                  {/* GD */}
                  <td
                    style={{
                      textAlign: "center",
                      fontWeight: 700,
                      color:
                        team.goal_difference > 0
                          ? "#1b5e20"
                          : team.goal_difference < 0
                          ? "#b71c1c"
                          : "#333",
                    }}
                  >
                    {team.goal_difference > 0 ? "+" : ""}
                    {team.goal_difference}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* TOP SCORERS */}
      <div style={{ borderTop: "2px solid #556b2f" }}>
        <div
          style={{
            background: "#556b2f",
            color: "#fff",
            padding: "8px",
            fontWeight: 700,
            textAlign: "center",
          }}
        >
          Top Scorers
        </div>

        <div style={{ padding: 8 }}>
          {data.top_scorers.map((p, i) => (
            <div
              key={i}
              style={{
                display: "grid",
                gridTemplateColumns: "28px 1fr auto",
                alignItems: "center",
                padding: "6px 8px",
                borderRadius: 6,
                marginBottom: 6,
                background:
                  i === 0
                    ? "rgba(255,215,0,0.25)"
                    : "rgba(255,255,255,0.15)",
                transition: "all 0.2s ease",
              }}
            >
              <div style={{ fontWeight: 700 }}>{i + 1}</div>

              <div style={{ fontSize: "0.95rem" }}>
                {p.player_name}
                <span style={{ opacity: 0.7 }}> ({p.team_name})</span>
              </div>

              <div style={{ fontWeight: 800 }}>{p.goals}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
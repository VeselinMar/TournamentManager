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

  if (loading)
    return <div style={{ padding: 12 }}>Loading leaderboard...</div>;

  if (!data)
    return <div style={{ padding: 12 }}>No leaderboard available</div>;

  return (
    <div
      style={{
        width: "100%",
        border: "1px solid #d6e2d6",
        borderRadius: 10,
        boxShadow: "0 4px 14px rgba(0,0,0,0.08)",
        overflow: "hidden",
        background: "#f3f7f3",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          background: "#1f3a1f",
          color: "#fff",
          padding: "12px",
          fontWeight: 800,
          textAlign: "center",
          letterSpacing: 1,
        }}
      >
        Leaderboard
      </div>

      {/* TABLE WRAPPER */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "clamp(0.85rem, 1vw, 1rem)",
            background: "#ffffff",
            color: "#1b1b1b",
            minWidth: 520,
          }}
        >
          <thead>
            <tr>
              {["#", "Team", "Pts", "W", "D", "L", "GF", "GA", "GD"].map(
                (h) => (
                  <th
                    key={h}
                    style={{
                      position: "sticky",
                      top: 0,
                      zIndex: 10,
                      backgroundColor: "#1f3a1f",
                      color: "#ffffff",
                      padding: "10px",
                      textAlign: "center",
                      borderBottom: "2px solid #d6e2d6",
                      fontWeight: 800,
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
                      ? "#fff8e1"
                      : idx % 2 === 0
                      ? "#ffffff"
                      : "#f6f8f6",
                    borderLeft: isTop
                      ? "4px solid #f9a825"
                      : "4px solid transparent",
                    transition: "background 0.2s ease",
                    cursor: "default",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor = "#e6f2e6")
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
                      padding: "8px",
                      color: isPodium ? "#1b3a00" : "#333",
                    }}
                  >
                    {idx + 1}
                  </td>

                  {/* Team */}
                  <td
                    style={{
                      padding: "8px",
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
                        padding: "8px",
                        fontVariantNumeric: "tabular-nums",
                        color: "#2b2b2b",
                      }}
                    >
                      {val}
                    </td>
                  ))}

                  {/* Goal Difference */}
                  <td
                    style={{
                      textAlign: "center",
                      fontWeight: 800,
                      color:
                        team.goal_difference > 0
                          ? "#1b5e20"
                          : team.goal_difference < 0
                          ? "#b71c1c"
                          : "#333",
                    }}
                  >
                    {team.goal_difference > 0
                      ? "+"
                      : ""}
                    {team.goal_difference}
                    {team.goal_difference > 0
                      ? " ▲"
                      : team.goal_difference < 0
                      ? " ▼"
                      : ""}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* TOP SCORERS */}
      <div style={{ borderTop: "1px solid #d6e2d6" }}>
        <div
          style={{
            background: "#1f3a1f",
            color: "#fff",
            padding: "10px",
            fontWeight: 800,
            textAlign: "center",
          }}
        >
          Top Scorers
        </div>

        <div style={{ padding: 10 }}>
          {data.top_scorers.map((p, i) => (
            <div
              key={i}
              style={{
                display: "grid",
                gridTemplateColumns: "28px 1fr auto",
                alignItems: "center",
                padding: "8px 10px",
                borderRadius: 8,
                marginBottom: 6,
                background: i === 0 ? "#fff3cd" : "#ffffff",
                border: "1px solid #e6e6e6",
                transition: "background 0.2s ease",
              }}
            >
              <div style={{ fontWeight: 800 }}>{i + 1}</div>

              <div style={{ fontSize: "0.95rem", color: "#1b1b1b" }}>
                {p.player_name}
                <span style={{ opacity: 0.7 }}>
                  {" "}
                  ({p.team_name})
                </span>
              </div>

              <div style={{ fontWeight: 900 }}>{p.goals}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
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

  if (loading) return <div>Loading leaderboard...</div>;
  if (!data) return <div>No leaderboard available</div>;

  return (
    <div>
      <h2>Leaderboard</h2>

      {/* Standings */}
      <h3>Standings</h3>
      <table>
        <thead>
          <tr>
            <th>Team</th>
            <th>Pts</th>
            <th>W</th>
            <th>D</th>
            <th>L</th>
            <th>GF</th>
            <th>GA</th>
            <th>GD</th>
          </tr>
        </thead>
        <tbody>
          {data.standings.map((team) => (
            <tr key={team.team_name}>
              <td>{team.team_name}</td>
              <td>{team.points}</td>
              <td>{team.wins}</td>
              <td>{team.draws}</td>
              <td>{team.losses}</td>
              <td>{team.goals_for}</td>
              <td>{team.goals_against}</td>
              <td>{team.goal_difference}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Top scorers */}
      <h3>Top Scorers</h3>
      <ul>
        {data.top_scorers.map((p, i) => (
          <li key={i}>
            {p.player_name} ({p.team_name}) — {p.goals}
          </li>
        ))}
      </ul>
    </div>
  );
}
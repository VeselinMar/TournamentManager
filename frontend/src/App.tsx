import { useEffect, useState } from "react";
import { getTournament } from "./api/tournament";
import type { Tournament } from "./types/tournament";

function App() {
  const [tournament, setTournament] = useState<Tournament | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTournament("turnir")
      .then((data) => setTournament(data))
      .catch((err) => {
        console.error(err);
        setError("Failed to fetch tournament");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;
  if (!tournament) return <div>No tournament found</div>;

  const visibleTabs = [
    tournament.show_leaderboard && "leaderboard",
    tournament.show_vendors && "vendors",
    tournament.show_side_events && "side events",
  ].filter(Boolean);

  return (
    <div>
      <h1>{tournament.name}</h1>
      <p>Visible Tabs: {visibleTabs.join(", ") || "none"}</p>
    </div>
  );
}

export default App;
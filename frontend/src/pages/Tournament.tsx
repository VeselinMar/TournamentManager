import { useEffect, useState } from "react";
import { Link, Outlet, useParams, useLocation } from "react-router-dom";
import { getTournament } from "../api/tournament";
import type { Tournament } from "../types/tournament";
import Header from "../components/schedule/Header"

export default function TournamentPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug!.toLowerCase();
  const [tournament, setTournament] = useState<Tournament | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const location = useLocation();

  useEffect(() => {
    getTournament(slug)
      .then(setTournament)
      .catch((err) => {
        console.error(err);
        setError("Failed to fetch tournament");
      })
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <div>Loading tournament...</div>;
  if (error) return <div>{error}</div>;
  if (!tournament) return <div>No tournament found</div>;

  const tabs = [
    { name: "Schedule", path: "schedule" },
    tournament.show_leaderboard && { name: "Leaderboard", path: "leaderboard" },
    tournament.show_vendors && { name: "Vendors", path: "vendors" },
    tournament.show_side_events && { name: "Side Events", path: "events" },
  ].filter(Boolean) as { name: string; path: string }[];

  return (
    <div>
      <Header name={tournament.name} isFinished={tournament.is_finished} />

      <nav style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
        {tabs.map((tab) => (
          <Link
            key={tab.path}
            to={tab.path}
            style={{
              fontWeight: location.pathname.endsWith(tab.path) ? "bold" : "normal",
            }}
          >
            {tab.name}
          </Link>
        ))}
      </nav>

      <main style={{ marginTop: "2rem" }}>
        <Outlet />
      </main>
    </div>
  );
}
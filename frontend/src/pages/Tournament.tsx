import { useEffect, useState } from "react";
import { Link, Outlet, useParams, useLocation } from "react-router-dom";
import { getTournament } from "../api/tournament";
import type { Tournament } from "../types/tournament";

export default function TournamentPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug!.toLowerCase(); // normalize slug
  const [tournament, setTournament] = useState<Tournament | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const location = useLocation(); // for highlighting active tab

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

  // Build visible tabs from booleans
  const tabs = [
    tournament.show_leaderboard && { name: "Leaderboard", path: "leaderboard" },
    tournament.show_vendors && { name: "Vendors", path: "vendors" },
    tournament.show_side_events && { name: "Side Events", path: "events" },
    // tournament.show_announcements && { name: "Announcements", path: "announcements" },
  ].filter(Boolean) as { name: string; path: string }[];

  return (
    <div>
      {/* Header */}
      <header>
        <h1>{tournament.name}</h1>
        <span>Status: {tournament.is_finished ? "Finished" : "In Progress"}</span>
        <span>Date: {tournament.tournament_date}</span>
      </header>

      {/* Tabs Navigation */}
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

      {/* Nested view */}
      <main style={{ marginTop: "2rem" }}>
        <Outlet />
      </main>
    </div>
  );
}
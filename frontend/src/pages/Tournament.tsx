import { useEffect, useState } from "react";
import { useNavigate, Outlet, useParams } from "react-router-dom";
import { getTournament } from "../api/tournament";
import type { Tournament } from "../types/tournament";
import Header from "../components/Header"
import Navbar from "../components/Navbar"

export default function TournamentPage() {
  const navigate = useNavigate();
  const params = useParams<{ slug: string }>();
  const slug = params.slug!.toLowerCase();
  const [tournament, setTournament] = useState<Tournament | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const handleSectionSelect = (path: string) => {
    navigate(path);
  };

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

  const sections = [
    { label: "Schedule", path: "schedule" },
    tournament.show_leaderboard && {
      label: "Leaderboard",
      path: "leaderboard",
    },
    tournament.show_vendors && {
      label: "Vendors",
      path: "vendors",
    },
    tournament.show_side_events && {
      label: "Side Events",
      path: "side-events",
    },
  ].filter(Boolean) as { label: string; path: string }[];

  return (
    <div>
      <Header name={tournament.name} isFinished={tournament.is_finished} />
      <Navbar sections={sections} onSelect={handleSectionSelect} />

      <main style={{ marginTop: "2rem" }}>
        <Outlet />
      </main>
    </div>
  );
}
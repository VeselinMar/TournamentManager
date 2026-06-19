import { useEffect, useState, useRef } from "react";
import { useNavigate, Outlet, useParams } from "react-router-dom";
import { getTournament } from "../api/tournament";
import type { Tournament } from "../types/tournament";
import Header from "../components/Header";
import Navbar from "../components/Navbar";
import SponsorCarousel from "../components/SponsorCarousel";

export default function TournamentPage() {
  const navigate = useNavigate();
  const params = useParams<{ slug: string }>();
  const slug = params.slug!.toLowerCase();
  const [tournament, setTournament] = useState<Tournament | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const topRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleSectionSelect = (section: string) => {
    navigate(`/${slug}/${section}`);
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
  
  useEffect(() => {
    if (tournament?.name) {
      document.title = tournament.name;
    }
  }, [tournament?.name]);

  if (loading) return <div>Loading tournament...</div>;
  if (error) return <div>{error}</div>;
  if (!tournament) return <div>No tournament found</div>;

  const sections = [
    { label: "Schedule", path: "schedule" },
    tournament.show_leaderboard && { label: "Leaderboard", path: "leaderboard" },
    tournament.show_vendors && { label: "Vendors", path: "vendors" },
    tournament.show_side_events && { label: "Side Events", path: "side-events" },
  ].filter(Boolean) as { label: string; path: string }[];

return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "97dvh",
      }}
    >
      <div ref={topRef}>
        <Header name={tournament.name} isFinished={tournament.is_finished} />
        <Navbar sections={sections} onSelect={handleSectionSelect} />
      </div>

      <main
        style={{
          flex: 1,
          display: "flex",
          justifyContent: "center",
          padding: "0.5rem 1rem",
          overflowY: "auto",
          overflowX: "hidden",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: 1400,
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <Outlet context={{ topRef, bottomRef }} />
        </div>
      </main>

      <div ref={bottomRef}>
        <SponsorCarousel sponsors={tournament.sponsors} direction="right" />
      </div>
    </div>
  );
}
import { createBrowserRouter, RouterProvider, useParams } from "react-router-dom";
import TournamentPage from "../pages/Tournament";
import Schedule from "../pages/Schedule";
import Leaderboard from "../pages/Leaderboard";
import Vendors from "../pages/Vendors";
import Events from "../pages/Events";

function ScheduleWrapper() {
  const { slug } = useParams<{ slug: string }>();
  if (!slug) return <div>No tournament selected</div>;
  return <Schedule slug={slug} />;
}

function LeaderboardWrapper() {
  const { slug } = useParams<{ slug: string }>();
  if (!slug) return <div>No tournament selected</div>;
  return <Leaderboard slug={slug} />;
}

function VendorsWrapper() {
  const { slug } = useParams<{ slug: string }>();
  if (!slug) return <div>No tournament selected</div>;
  return <Vendors slug={slug} />;
}

function EventsWrapper() {
  const { slug } = useParams<{ slug: string }>();
  if (!slug) return <div>No tournament selected</div>;
  return <Events slug={slug} />;
}


const router = createBrowserRouter([
  {
    path: "/:slug",
    element: <TournamentPage />,
    children: [
      { index: true, element: <ScheduleWrapper />},
      { path: "schedule", element: <ScheduleWrapper /> },
      { path: "leaderboard", element: <LeaderboardWrapper /> },
      { path: "vendors", element: <VendorsWrapper /> },
      { path: "side-events", element: <EventsWrapper /> },
    ],
  },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
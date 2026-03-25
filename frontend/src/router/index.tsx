import { createBrowserRouter, RouterProvider } from "react-router-dom";
import TournamentPage from "../pages/Tournament";
import Schedule from "../pages/Schedule";
import Leaderboard from "../pages/Leaderboard";
import Vendors from "../pages/Vendors";
import Events from "../pages/Events";

const router = createBrowserRouter([
  {
    path: "/:slug",
    element: <TournamentPage />,
    children: [
      { path: "schedule", element: <Schedule /> },
      { path: "leaderboard", element: <Leaderboard /> },
      { path: "vendors", element: <Vendors /> },
      { path: "events", element: <Events /> },
    ],
  },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
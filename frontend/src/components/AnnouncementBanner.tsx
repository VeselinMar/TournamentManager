import { useEffect, useState } from "react";
import apiClient from "../api/client";
import type { Announcement } from "../types/announcement";

interface Props {
  slug: string;
}

export default function AnnouncementBanner({ slug }: Props) {
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [dismissed, setDismissed] = useState(false);

  const fetchAnnouncements = async () => {
    try {
      const res = await apiClient.get<Announcement[]>(
        `/tournaments/${slug}/announcements/`
      );

      const now = new Date();

      // find most recent active announcement
      const active = res.data
        .filter((a) => a.is_active)
        .filter((a) => new Date(a.starts_at) <= now && new Date(a.ends_at) >= now)
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime()
        )[0];

      setAnnouncement(active || null);
      setDismissed(false); // reset if new announcement appears
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchAnnouncements();
    const interval = setInterval(fetchAnnouncements, 15000); // 15s polling
    return () => clearInterval(interval);
  }, [slug]);

  if (!announcement || dismissed) return null;

  return (
    <div
      style={{
        background: "#fffae6",
        padding: "1rem",
        borderBottom: "1px solid #ccc",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <div>{announcement.message}</div>

      <button onClick={() => setDismissed(true)}>✕</button>
    </div>
  );
}
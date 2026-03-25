import { useEffect, useState } from "react";
import apiClient from "../api/client";
import type { Event } from "../types/events";

interface Props {
  slug: string;
}

export default function Events({ slug }: Props) {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchEvents = async () => {
    try {
      const res = await apiClient.get<Event[]>(
        `/tournaments/${slug}/side-events/`
      );

      const sorted = res.data
        .filter((e) => e.is_active) // optional but recommended
        .sort(
          (a, b) =>
            new Date(a.start_time).getTime() -
            new Date(b.start_time).getTime()
        );

      setEvents(sorted);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [slug]);

  if (loading) return <div>Loading events...</div>;
  if (!events.length) return <div>No events scheduled</div>;

  return (
    <div>
      <h2>Side Events</h2>

      {events.map((e, index) => (
        <div key={`${e.name}-${e.start_time}-${index}`} style={{ marginBottom: "1rem" }}>
          <strong>
            {new Date(e.start_time).toLocaleTimeString()} -{" "}
            {new Date(e.end_time).toLocaleTimeString()}
          </strong>
          {" — "}
          {e.name}

          {e.description && (
            <div style={{ fontSize: "0.9rem", marginTop: "0.25rem" }}>
              {e.description}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
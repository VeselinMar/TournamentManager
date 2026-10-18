import { useCallback, useEffect, useState } from "react";
import apiClient from "../api/client";
import type { ScheduleResponse } from "../types/match";
import TimelineTable from "../components/schedule/TimelineTable";

interface Props {
  slug: string;
}

// Results and knockout pairings change during the day
const REFRESH_MS = 60000;

export default function Schedule({ slug }: Props) {
  const [data, setData] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSchedule = useCallback(async () => {
    try {
      const res = await apiClient.get<ScheduleResponse>(
        `/tournaments/${slug}/schedule/`
      );
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    const first = window.setTimeout(fetchSchedule, 0);
    const interval = window.setInterval(fetchSchedule, REFRESH_MS);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(interval);
    };
  }, [fetchSchedule]);

  if (loading) return <div>Loading schedule...</div>;
  if (!data) return <div>No data</div>;

  return (
    <div>
      <TimelineTable
        timeline={data.timeline}
        fieldNames={data.field_names}
      />
    </div>
  );
}

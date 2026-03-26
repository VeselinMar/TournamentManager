import { useEffect, useState } from "react";
import apiClient from "../api/client";
import type { ScheduleResponse } from "../types/match";
import TimelineTable from "../components/schedule/TimelineTable";

interface Props {
  slug: string;
}

export default function Schedule({ slug }: Props) {
  const [data, setData] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSchedule = async () => {
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
  };

  useEffect(() => {
    fetchSchedule();
  }, [slug]);

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
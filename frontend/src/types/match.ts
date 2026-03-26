export type TimelineMatch = {
  id: number;
  home_team: string;
  away_team: string;
  field: string;
  home_score: number;
  away_score: number;
  is_finished: boolean;
};

export type TimelineRow = {
  time: string;
  matches: (TimelineMatch | null)[];
};

export type ScheduleResponse = {
  field_names: string[];
  timeline: TimelineRow[];
  current_matches: TimelineMatch[];
};
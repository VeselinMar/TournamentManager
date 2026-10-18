export type TimelineMatch = {
  id: number;
  stage: "group" | "knockout";
  group: string | null;
  round: number | null;
  round_label: string;
  is_third_place: boolean;
  bracket_position: number | null;
  /** Team name, or a placeholder such as "Winner SF 1" while undecided */
  home_team: string;
  away_team: string;
  home_placeholder: boolean;
  away_placeholder: boolean;
  field: string;
  start_time: string;
  home_score: number;
  away_score: number;
  home_penalties: number | null;
  away_penalties: number | null;
  decided_by: "regular" | "extra_time" | "penalties" | null;
  winner: string | null;
  is_finished: boolean;
};

export type TimelineRow = {
  time: string;
  datetime: string;
  matches: (TimelineMatch | null)[];
};

export type ScheduleResponse = {
  field_names: string[];
  timeline: TimelineRow[];
  current_matches: TimelineMatch[];
};

export type BracketRound = {
  round: number;
  label: string;
  matches: TimelineMatch[];
};

export type BracketResponse = {
  format: string;
  rounds: BracketRound[];
};

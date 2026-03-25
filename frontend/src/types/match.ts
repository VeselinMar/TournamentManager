export interface Match {
  id: number;
  home_team: string;
  away_team: string;
  field: string;
  start_time: string;
  home_score: number;
  away_score: number;
  is_finished: boolean;
}
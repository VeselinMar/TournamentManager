export type Tournament = {
  slug: string;
  name: string;
  is_finished: boolean;
  tournament_date: string;
  show_leaderboard: boolean;
  show_vendors: boolean;
  show_side_events: boolean;
  show_announcements: boolean;
  sponsors: any[];
};
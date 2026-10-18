export type Sponsor = {
  id: number;
  name: string;
  image_url: string | null;
  link_url: string | null;
  /** Counts the click, then redirects to link_url */
  click_url: string | null;
};

export type Tournament = {
  slug: string;
  name: string;
  is_finished: boolean;
  tournament_date: string;
  show_leaderboard: boolean;
  show_vendors: boolean;
  show_side_events: boolean;
  show_announcements: boolean;
  tiebreak_rule: "head_to_head" | "goal_difference";
  format: "round_robin" | "groups_knockout";
  sponsors: Sponsor[];
};

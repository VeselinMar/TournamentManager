export type TeamStanding = {
  rank: number;
  team_name: string;
  points: number;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  qualifies: boolean;
};

export type GroupStanding = {
  name: string | null;
  qualifiers: number;
  standings: TeamStanding[];
};

export type TopScorer = {
  player_name: string;
  team_name: string;
  goals: number;
};

export type LeaderboardResponse = {
  format: "round_robin" | "groups_knockout";
  standings: TeamStanding[];
  groups: GroupStanding[];
  best_placed_qualifiers: number;
  top_scorers: TopScorer[];
};

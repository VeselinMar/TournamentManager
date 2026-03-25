export type TeamStanding = {
  team_name: string;
  points: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
};

export type TopScorer = {
  player_name: string;
  team_name: string;
  goals: number;
};

export type LeaderboardResponse = {
  standings: TeamStanding[];
  top_scorers: TopScorer[];
};
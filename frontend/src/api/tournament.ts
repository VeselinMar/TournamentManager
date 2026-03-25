import apiClient from "./client";
import type { Tournament } from "../types/tournament";

export const getTournament = async (slug: string) => {
  const response = await apiClient.get<Tournament>(
    `/tournaments/${slug}/`
  );
  return response.data;
};
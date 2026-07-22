import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";

export interface RoomScore {
  room_id: number;
  year_month: string;
  total_score: number;
  max_score: number;
  score_pct: number;
  inspection_count: number;
}

export interface IssueFrequency {
  item_id: number;
  item_name_snapshot: string;
  year_month: string;
  score_zero_count: number;
}

function currentMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function useLowestRooms(yearMonth?: string, limit = 3) {
  const ym = yearMonth || currentMonth();
  return useQuery({
    queryKey: ["analytics", "lowest-rooms", ym, limit],
    queryFn: () =>
      apiRequest<RoomScore[]>(
        `/api/analytics/lowest-rooms?year_month=${ym}&limit=${limit}`,
      ),
  });
}

export function useTopIssues(yearMonth?: string, limit = 10) {
  const ym = yearMonth || currentMonth();
  return useQuery({
    queryKey: ["analytics", "top-issues", ym, limit],
    queryFn: () =>
      apiRequest<IssueFrequency[]>(
        `/api/analytics/top-issues?year_month=${ym}&limit=${limit}`,
      ),
  });
}

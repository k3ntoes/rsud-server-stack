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

export function currentWeekMonth() {
  return new Date().toISOString().slice(0, 7);
}

export function useLowestRooms(yearMonth?: string, limit = 3) {
  const ym = yearMonth || currentWeekMonth();
  return useQuery({
    queryKey: ["analytics", "lowest-rooms", ym, limit],
    queryFn: () =>
      apiRequest<RoomScore[]>(
        `/api/analytics/lowest-rooms?year_month=${ym}&limit=${limit}`,
      ),
  });
}

export function useTopIssues(yearMonth?: string, limit = 10) {
  const ym = yearMonth || currentWeekMonth();
  return useQuery({
    queryKey: ["analytics", "top-issues", ym, limit],
    queryFn: () =>
      apiRequest<IssueFrequency[]>(
        `/api/analytics/top-issues?year_month=${ym}&limit=${limit}`,
      ),
  });
}

export interface DashboardSummary {
  monthly_inspection_count: number;
  avg_score_pct: number;
}

export function useDashboardSummary(yearMonth?: string) {
  const ym = yearMonth || currentWeekMonth();
  return useQuery({
    queryKey: ["analytics", "summary", ym],
    queryFn: () =>
      apiRequest<DashboardSummary>(
        `/api/analytics/summary?year_month=${ym}`,
      ),
  });
}

export interface DashboardAll {
  pending_count: number;
  total_rooms: number;
  monthly_inspection_count: number;
  avg_score_pct: number;
  /** Effective month the stats refer to; falls back to the latest month with
   * data when the current month is empty, or null when there is no data. */
  year_month: string | null;
}

export function useDashboardData(yearMonth?: string) {
  const ym = yearMonth || currentWeekMonth();
  return useQuery({
    queryKey: ["dashboard", ym],
    queryFn: () =>
      apiRequest<DashboardAll>(
        `/api/analytics/dashboard?year_month=${ym}`,
      ),
  });
}

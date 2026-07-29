import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";
import type { PaginatedResult } from "../components/DataTable";

export interface InspectionPhoto {
  id: number;
  photo_file_name: string;
  thumbnail_file_name: string | null;
  sort_order: number;
}

export interface InspectionDetail {
  id: number;
  item_id: number;
  item_name_snapshot: string;
  score: number;
  photos: InspectionPhoto[];
}

export interface InspectionOut {
  id: number;
  room_id: number;
  inspector_id: number;
  status: string;
  business_date: string;
  local_timestamp: string;
  rejection_reason: string | null;
  created_at: string;
  details: InspectionDetail[];
}

export interface InspectionListItem {
  id: number;
  room_id: number;
  inspector_id: number;
  status: string;
  business_date: string;
  created_at: string;
  detail_count: number;
}

interface ListParams {
  status?: string;
  room_id?: number;
  business_date?: string;
  show_all?: string;
  search?: string;
}

export function useInspections(params: ListParams = {}, page = 0, perPage = 20, sortBy?: string, sortOrder?: string) {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.room_id) qs.set("room_id", String(params.room_id));
  if (params.business_date) qs.set("business_date", params.business_date);
  if (params.show_all) qs.set("show_all", params.show_all);
  if (params.search) qs.set("search", params.search);
  qs.set("page", String(page + 1));
  qs.set("per_page", String(perPage));
  if (sortBy) qs.set("sort_by", sortBy);
  if (sortOrder) qs.set("sort_order", sortOrder);
  const query = qs.toString();

  return useQuery({
    queryKey: ["inspections", params, page, perPage, sortBy, sortOrder],
    queryFn: () => apiRequest<PaginatedResult<InspectionListItem>>(`/api/inspections?${query}`),
  });
}

export function useInspection(id: number) {
  return useQuery({
    queryKey: ["inspection", id],
    queryFn: () => apiRequest<InspectionOut>(`/api/inspections/${id}`),
    enabled: !!id,
  });
}

export function useApproveInspection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiRequest<InspectionOut>(`/api/inspections/${id}/approve`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["inspections"] });
      qc.invalidateQueries({ queryKey: ["inspection"] });
    },
  });
}

export function useRejectInspection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      apiRequest<InspectionOut>(`/api/inspections/${id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rejection_reason: reason }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["inspections"] });
      qc.invalidateQueries({ queryKey: ["inspection"] });
    },
  });
}

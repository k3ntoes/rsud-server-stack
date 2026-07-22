import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";

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
}

export function useInspections(params: ListParams = {}) {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.room_id) qs.set("room_id", String(params.room_id));
  if (params.business_date) qs.set("business_date", params.business_date);
  const query = qs.toString();

  return useQuery({
    queryKey: ["inspections", params],
    queryFn: () => apiRequest<InspectionListItem[]>(`/api/inspections${query ? `?${query}` : ""}`),
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

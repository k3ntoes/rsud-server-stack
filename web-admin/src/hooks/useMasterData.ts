import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";

export interface Room {
  id: number;
  name: string;
  is_active: boolean;
}

export interface Item {
  id: number;
  name: string;
  is_active: boolean;
}

// ── Rooms ──

export function useRooms() {
  return useQuery({
    queryKey: ["rooms"],
    queryFn: () => apiRequest<Room[]>("/api/rooms"),
  });
}

export function useCreateRoom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiRequest<Room>("/api/rooms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rooms"] }),
  });
}

export function useUpdateRoom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      apiRequest<Room>(`/api/rooms/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rooms"] }),
  });
}

export function useDeleteRoom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiRequest<void>(`/api/rooms/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rooms"] }),
  });
}

// ── Inspection Items ──

export function useItems() {
  return useQuery({
    queryKey: ["items"],
    queryFn: () => apiRequest<Item[]>("/api/inspection-items"),
  });
}

export function useCreateItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiRequest<Item>("/api/inspection-items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["items"] }),
  });
}

export function useUpdateItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      apiRequest<Item>(`/api/inspection-items/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["items"] }),
  });
}

export function useDeleteItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiRequest<void>(`/api/inspection-items/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["items"] }),
  });
}

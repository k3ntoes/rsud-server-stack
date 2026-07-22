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

// ── Mutation factories ──

function useCreateMutation<T>(path: string, queryKey: string[]) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiRequest<T>(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey }),
  });
}

function useUpdateMutation<T>(path: string, queryKey: string[]) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      apiRequest<T>(`${path}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey }),
  });
}

function useDeleteMutation(path: string, queryKey: string[]) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiRequest<void>(`${path}/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey }),
  });
}

// ── Rooms ──

export function useRooms() {
  return useQuery({
    queryKey: ["rooms"],
    queryFn: () => apiRequest<Room[]>("/api/rooms"),
  });
}

export const useCreateRoom = () => useCreateMutation<Room>("/api/rooms", ["rooms"]);
export const useUpdateRoom = () => useUpdateMutation<Room>("/api/rooms", ["rooms"]);
export const useDeleteRoom = () => useDeleteMutation("/api/rooms", ["rooms"]);

// ── Inspection Items ──

export function useItems() {
  return useQuery({
    queryKey: ["items"],
    queryFn: () => apiRequest<Item[]>("/api/inspection-items"),
  });
}

export const useCreateItem = () => useCreateMutation<Item>("/api/inspection-items", ["items"]);
export const useUpdateItem = () => useUpdateMutation<Item>("/api/inspection-items", ["items"]);
export const useDeleteItem = () => useDeleteMutation("/api/inspection-items", ["items"]);

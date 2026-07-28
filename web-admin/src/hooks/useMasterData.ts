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

// ── Room-Items (pivot) ──

export interface RoomItem {
  id: number;
  room_id: number;
  item_id: number;
  created_at: string;
}

export function useRoomItemsByRoom(roomId: number) {
  return useQuery({
    queryKey: ["room-items", "room", roomId],
    queryFn: () => apiRequest<RoomItem[]>(`/api/rooms/${roomId}/items`),
    enabled: !!roomId,
  });
}

export function useRoomsByItem(itemId: number) {
  return useQuery({
    queryKey: ["room-items", "item", itemId],
    queryFn: () => apiRequest<RoomItem[]>(`/api/inspection-items/${itemId}/rooms`),
    enabled: !!itemId,
  });
}

export function useAssignItemToRoom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ roomId, itemId }: { roomId: number; itemId: number }) =>
      apiRequest<RoomItem>(`/api/rooms/${roomId}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: itemId }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["room-items"] });
      qc.invalidateQueries({ queryKey: ["rooms"] });
    },
  });
}

export function useUnassignItemFromRoom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ roomId, itemId }: { roomId: number; itemId: number }) =>
      apiRequest<void>(`/api/rooms/${roomId}/items/${itemId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["room-items"] });
      qc.invalidateQueries({ queryKey: ["rooms"] });
    },
  });
}

export function useAssignRoomToItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, roomId }: { itemId: number; roomId: number }) =>
      apiRequest<RoomItem>(`/api/inspection-items/${itemId}/rooms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ room_id: roomId }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["room-items"] });
      qc.invalidateQueries({ queryKey: ["items"] });
    },
  });
}

export function useUnassignRoomFromItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, roomId }: { itemId: number; roomId: number }) =>
      apiRequest<void>(`/api/inspection-items/${itemId}/rooms/${roomId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["room-items"] });
      qc.invalidateQueries({ queryKey: ["items"] });
    },
  });
}

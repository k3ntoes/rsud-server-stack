import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";

export interface User {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

const ROLES = [
  { value: "admin_ppi", label: "Admin PPI" },
  { value: "supervisor", label: "Supervisor" },
  { value: "inspector", label: "Inspector" },
];

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: () => apiRequest<User[]>("/api/auth/users"),
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { username: string; password: string; role: string }) =>
      apiRequest<User>("/api/auth/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { id: number; username?: string; role?: string; is_active?: boolean }) =>
      apiRequest<User>(`/api/auth/users/${data.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: data.username,
          role: data.role,
          is_active: data.is_active,
        }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiRequest<void>(`/api/auth/users/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: { old_password: string; new_password: string }) =>
      apiRequest<{ message: string }>("/api/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
  });
}

export function useAdminResetPassword() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { user_id: number; new_password: string }) =>
      apiRequest<{ message: string }>(`/api/auth/users/${data.user_id}/reset-password`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: data.new_password }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useInspectorPerformance(yearMonth?: string) {
  const ym = yearMonth || new Date().toISOString().slice(0, 7);
  return useQuery({
    queryKey: ["analytics", "inspector-performance", ym],
    queryFn: () =>
      apiRequest<{ inspector_id: number; username: string; total_inspections: number }[]>(
        `/api/analytics/inspector-performance?year_month=${ym}`,
      ),
  });
}

export { ROLES };

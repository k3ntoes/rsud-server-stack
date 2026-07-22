import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/inspections",
  component: () => (
    <div className="rounded-xl border bg-white p-8 text-center text-gray-400">
      <p className="text-lg">✅</p>
      <p className="mt-2 text-sm">Approval inspeksi — akan diimplementasikan di Phase 5C.</p>
    </div>
  ),
});

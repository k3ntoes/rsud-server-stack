import { useState, useMemo } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import { useInspectorPerformance, useUsers } from "../hooks/useUsers";
import { useRoomsAll } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/inspectors",
  component: InspectorsPage,
});

function InspectorsPage() {
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const { data: inspectors, isLoading, error } = useInspectorPerformance(month);
  const { data: users } = useUsers(0, 100);
  const { data: allRooms } = useRoomsAll();

  // Build map: userId → room names (from user.room_ids)
  const userRoomMap = useMemo(() => {
    const roomById = new Map(allRooms?.map((r) => [r.id, r.name]) ?? []);
    const map = new Map<number, string[]>();
    for (const u of users?.items ?? []) {
      if (!u.room_ids?.length) continue;
      const names = u.room_ids.map((id) => roomById.get(id)).filter(Boolean) as string[];
      if (names.length > 0) map.set(u.id, names);
    }
    return map;
  }, [users, allRooms]);

  const maxInspections = Math.max(
    ...(inspectors?.map((i) => i.total_inspections) ?? [0]),
    1,
  );

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Kinerja Inspector</h1>
          <p className="page-subtitle">
            Jumlah inspeksi yang telah disetujui per inspector
          </p>
        </div>
        <input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="input-plan w-44"
        />
      </div>

      <div className="card-plan p-6">
        {isLoading ? (
          <div>
            <div className="skeleton mb-4 h-4 w-full" />
            <div className="skeleton mb-4 h-4 w-3/4" />
            <div className="skeleton h-4 w-5/6" />
          </div>
        ) : error ? (
          <div className="empty-state">
            <span className="empty-state-icon">⚠️</span>
            <p className="empty-state-text">Gagal memuat data.</p>
          </div>
        ) : !inspectors?.length ? (
          <div className="empty-state py-8">
            <span className="empty-state-icon">📋</span>
            <p className="empty-state-text">
              Belum ada data inspeksi untuk bulan ini.
            </p>
          </div>
        ) : (
          <div>
            {inspectors.map((insp) => {
              const pct = (insp.total_inspections / maxInspections) * 100;
              const roomNames = userRoomMap.get(insp.inspector_id) ?? [];
              return (
                <div key={insp.inspector_id} className="mb-6 last:mb-0">
                  <div className="mb-1 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-navy-100 text-sm font-semibold text-navy-700">
                        {insp.username.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium text-ink">{insp.username}</span>
                    </div>
                    <span className="text-sm font-semibold text-ink">
                      {insp.total_inspections} inspeksi
                    </span>
                  </div>
                  {roomNames.length > 0 && (
                    <div className="mb-2 flex flex-wrap gap-1">
                      {roomNames.map((name) => (
                        <span
                          key={name}
                          className="inline-flex items-center rounded-full bg-navy-50 px-2 py-0.5 text-xs font-medium text-navy-600 ring-1 ring-inset ring-navy-200/50"
                        >
                          🏥 {name}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-navy-100/60">
                    <div
                      className="h-full rounded-full bg-teal-500 transition-all duration-700 ease-out"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

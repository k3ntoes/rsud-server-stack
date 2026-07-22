import { useState } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import { useLowestRooms, useTopIssues, type RoomScore, type IssueFrequency } from "../hooks/useAnalytics";
import { useRooms } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/analytics",
  component: AnalyticsPage,
});

function currentMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function Bar({ value, max, label, color }: { value: number; max: number; label: string; color: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="mb-3">
      <div className="mb-1 flex justify-between text-sm">
        <span className="text-gray-700">{label}</span>
        <span className="font-medium text-gray-900">{value}</span>
      </div>
      <div className="h-3 w-full rounded-full bg-gray-100">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function ScoreBar({ room, roomName }: { room: RoomScore; roomName: string }) {
  const pct = room.score_pct;
  const color =
    pct < 60 ? "bg-red-500" : pct < 80 ? "bg-amber-500" : "bg-green-500";
  return (
    <Bar value={room.score_pct} max={100} label={roomName} color={color} />
  );
}

function IssueBar({ issue, max }: { issue: IssueFrequency; max: number }) {
  return (
    <Bar value={issue.score_zero_count} max={max} label={issue.item_name_snapshot} color="bg-red-400" />
  );
}

function AnalyticsPage() {
  const [month, setMonth] = useState(currentMonth());
  const { data: rooms } = useRooms();
  const { data: lowestRooms, isLoading: loadingRooms } = useLowestRooms(month, 3);
  const { data: topIssues, isLoading: loadingIssues } = useTopIssues(month, 10);

  const roomMap = new Map(rooms?.map((r) => [r.id, r.name]) ?? []);
  const maxIssue = Math.max(...(topIssues?.map((i) => i.score_zero_count) ?? [0]), 1);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Analitik</h1>
        <input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Lowest-rated rooms */}
        <div className="rounded-xl border bg-white p-6">
          <h2 className="mb-4 text-base font-semibold text-gray-900">
            Ruangan dengan Skor Terendah
          </h2>
          {loadingRooms ? (
            <p className="text-sm text-gray-400">Memuat...</p>
          ) : !lowestRooms?.length ? (
            <p className="text-sm text-gray-400">Belum ada data untuk bulan ini.</p>
          ) : (
            lowestRooms.map((r) => (
              <ScoreBar
                key={r.room_id}
                room={r}
                roomName={roomMap.get(r.room_id) ?? `Ruangan #${r.room_id}`}
              />
            ))
          )}
          {lowestRooms && lowestRooms.length > 0 && (
            <p className="mt-2 text-xs text-gray-400">
              Skor dihitung dari total inspeksi bulan ini.
            </p>
          )}
        </div>

        {/* Top issues */}
        <div className="rounded-xl border bg-white p-6">
          <h2 className="mb-4 text-base font-semibold text-gray-900">
            Item Paling Sering Bermasalah (Skor 0)
          </h2>
          {loadingIssues ? (
            <p className="text-sm text-gray-400">Memuat...</p>
          ) : !topIssues?.length ? (
            <p className="text-sm text-gray-400">Belum ada data untuk bulan ini.</p>
          ) : (
            topIssues.map((i) => (
              <IssueBar key={i.item_id} issue={i} max={maxIssue} />
            ))
          )}
          {topIssues && topIssues.length > 0 && (
            <p className="mt-2 text-xs text-gray-400">
              Item dengan skor 0 (Berisiko) paling sering muncul.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import {
  useLowestRooms,
  useTopIssues,
  currentMonth,
  type RoomScore,
  type IssueFrequency,
} from "../hooks/useAnalytics";
import { useRooms } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/analytics",
  component: AnalyticsPage,
});

function Bar({
  value,
  max,
  label,
  indicator,
}: {
  value: number;
  max: number;
  label: string;
  indicator: string;
}) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="mb-4">
      <div className="mb-1.5 flex justify-between text-sm">
        <span className="text-ink-muted">{label}</span>
        <span className="font-semibold text-ink">{value}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-navy-100/60">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${indicator}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function ScoreBar({
  room,
  roomName,
}: {
  room: RoomScore;
  roomName: string;
}) {
  const pct = room.score_pct;
  const indicator =
    pct < 60
      ? "bg-danger"
      : pct < 80
        ? "bg-warning"
        : "bg-success";
  return (
    <Bar value={room.score_pct} max={100} label={roomName} indicator={indicator} />
  );
}

function IssueBar({
  issue,
  max,
}: {
  issue: IssueFrequency;
  max: number;
}) {
  return (
    <Bar
      value={issue.score_zero_count}
      max={max}
      label={issue.item_name_snapshot}
      indicator="bg-danger/70"
    />
  );
}

function AnalyticsPage() {
  const [month, setMonth] = useState(currentMonth());
  const { data: rooms } = useRooms();
  const {
    data: lowestRooms,
    isLoading: loadingRooms,
  } = useLowestRooms(month, 3);
  const {
    data: topIssues,
    isLoading: loadingIssues,
  } = useTopIssues(month, 10);

  const roomMap = new Map(rooms?.map((r) => [r.id, r.name]) ?? []);
  const maxIssue = Math.max(
    ...(topIssues?.map((i) => i.score_zero_count) ?? [0]),
    1,
  );

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Analitik</h1>
          <p className="page-subtitle">
            Ringkasan performa inspeksi kebersihan
          </p>
        </div>
        <input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="input-plan w-44"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Lowest-rated rooms */}
        <div className="card-plan p-6">
          <div className="mb-1 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-plan bg-navy-50 text-xs">
              📉
            </div>
            <h2 className="text-base font-semibold text-ink">
              Ruangan dengan Skor Terendah
            </h2>
          </div>
          <div className="mt-5">
            {loadingRooms ? (
              <div>
                <div className="skeleton mb-4 h-4 w-full" />
                <div className="skeleton mb-4 h-4 w-3/4" />
                <div className="skeleton h-4 w-5/6" />
              </div>
            ) : !lowestRooms?.length ? (
              <div className="empty-state py-8">
                <span className="empty-state-icon">📊</span>
                <p className="empty-state-text">
                  Belum ada data untuk bulan ini.
                </p>
              </div>
            ) : (
              lowestRooms.map((r) => (
                <ScoreBar
                  key={r.room_id}
                  room={r}
                  roomName={
                    roomMap.get(r.room_id) ?? `Ruangan #${r.room_id}`
                  }
                />
              ))
            )}
          </div>
          {lowestRooms && lowestRooms.length > 0 && (
            <p className="mt-2 text-xs text-ink-subtle">
              Skor dihitung dari total inspeksi bulan ini.
            </p>
          )}
        </div>

        {/* Top issues */}
        <div className="card-plan p-6">
          <div className="mb-1 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-plan bg-danger-muted text-xs">
              🔴
            </div>
            <h2 className="text-base font-semibold text-ink">
              Item Paling Sering Bermasalah
            </h2>
          </div>
          <div className="mt-5">
            {loadingIssues ? (
              <div>
                <div className="skeleton mb-4 h-4 w-full" />
                <div className="skeleton mb-4 h-4 w-3/4" />
                <div className="skeleton h-4 w-5/6" />
              </div>
            ) : !topIssues?.length ? (
              <div className="empty-state py-8">
                <span className="empty-state-icon">📊</span>
                <p className="empty-state-text">
                  Belum ada data untuk bulan ini.
                </p>
              </div>
            ) : (
              topIssues.map((i) => (
                <IssueBar key={i.item_id} issue={i} max={maxIssue} />
              ))
            )}
          </div>
          {topIssues && topIssues.length > 0 && (
            <p className="mt-2 text-xs text-ink-subtle">
              Item dengan skor 0 (Berisiko) paling sering muncul.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

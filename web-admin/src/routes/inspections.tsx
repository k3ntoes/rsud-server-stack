import { useState } from "react";
import { createRoute, useNavigate } from "@tanstack/react-router";
import type { PaginationState, SortingState, ColumnDef, OnChangeFn } from "@tanstack/react-table";
import { protectedRoute } from "./_protected";
import DataTable from "../components/DataTable";
import { useInspections, type InspectionListItem } from "../hooks/useInspections";
import { useRoomsAll } from "../hooks/useMasterData";
import { useDebounce } from "../hooks/useDebounce";
import { statusBadge } from "./inspection-detail";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/inspections",
  component: InspectionsPage,
});

const STATUSES = ["", "PENDING", "APPROVED", "REJECTED"] as const;
const STATUS_LABELS: Record<string, string> = {
  "": "Semua",
  PENDING: "Menunggu",
  APPROVED: "Disetujui",
  REJECTED: "Ditolak",
};

function InspectionsPage() {
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const [showAll, setShowAll] = useState(false);
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  });
  const [sorting, setSorting] = useState<SortingState>([]);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);

  const params = {
    ...(statusFilter ? { status: statusFilter } : {}),
    show_all: showAll ? "true" : undefined,
    ...(debouncedSearch ? { search: debouncedSearch } : {}),
  };

  const activeSort = sorting[0];
  const sortBy = activeSort?.id;
  const sortOrder = activeSort?.desc ? "desc" : "asc";

  const { data: result, isLoading, error } = useInspections(
    params,
    pagination.pageIndex,
    pagination.pageSize,
    sortBy,
    sortOrder,
  );

  const handleSortingChange: OnChangeFn<SortingState> = (updater) => {
    setSorting(updater);
    setPagination((p) => ({ ...p, pageIndex: 0 }));
  };
  const { data: rooms } = useRoomsAll();
  const navigate = useNavigate();

  const roomMap = new Map(rooms?.map((r) => [r.id, r.name]) ?? []);

  const columns: ColumnDef<InspectionListItem>[] = [
    {
      accessorKey: "business_date",
      header: "Tanggal",
      cell: ({ row }) => (
        <span className="text-ink-muted">{row.original.business_date}</span>
      ),
    },
    {
      id: "room_name",
      header: "Ruangan",
      cell: ({ row }) => (
        <span className="font-medium text-ink">
          {roomMap.get(row.original.room_id) ?? `Ruangan #${row.original.room_id}`}
        </span>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => statusBadge(row.original.status),
    },
    {
      accessorKey: "detail_count",
      header: () => <span className="text-center block">Item</span>,
      cell: ({ row }) => (
        <span className="block text-center text-ink-muted">
          {row.original.detail_count}
        </span>
      ),
    },
    {
      id: "actions",
      header: () => <span className="text-right block">Aksi</span>,
      cell: ({ row }) => (
        <div className="text-right">
          <button
            onClick={() =>
              navigate({
                to: "/inspections/$inspectionId",
                params: { inspectionId: String(row.original.id) },
              })
            }
            className="btn-ghost text-xs"
          >
            Detail
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Inspeksi</h1>
          <p className="page-subtitle">
            Daftar inspeksi kebersihan harian
          </p>
        </div>
      </div>

      {/* Status filter tabs */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="tab-group">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => {
              setStatusFilter(s);
              setPagination((p) => ({ ...p, pageIndex: 0 }));
            }}
            className={statusFilter === s ? "tab-item-active" : "tab-item"}
          >
            {STATUS_LABELS[s]}
          </button>
        )        )}
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-ink-muted">
          <input
            type="checkbox"
            checked={showAll}
            onChange={(e) => {
              setShowAll(e.target.checked);
              setPagination((p) => ({ ...p, pageIndex: 0 }));
            }}
            className="h-4 w-4 rounded border-navy-300 text-teal-600 focus:ring-teal-500"
          />
          Lihat semua ruangan
        </label>
      </div>

      <div className="card-plan overflow-hidden">
        <div className="border-b border-navy-100/50 px-4 py-3">
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPagination((p) => ({ ...p, pageIndex: 0 }));
            }}
            placeholder="Cari inspeksi..."
            className="input-plan max-w-xs"
          />
        </div>
        <DataTable
          columns={columns}
          data={result?.items ?? []}
          pagination={pagination}
          totalPages={result?.total_pages ?? 1}
          total={result?.total ?? 0}
          onPaginationChange={setPagination}
          sorting={sorting}
          onSortingChange={handleSortingChange}
          isLoading={isLoading}
          error={error}
          emptyIcon="✅"
          emptyText={
            statusFilter === "PENDING"
              ? "Tidak ada inspeksi menunggu."
              : "Belum ada data inspeksi."
          }
        />
      </div>
    </div>
  );
}

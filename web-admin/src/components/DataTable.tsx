import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
  type PaginationState,
  type SortingState,
  type OnChangeFn,
} from "@tanstack/react-table";
import { ChevronLeftIcon, ChevronRightIcon, SortAscIcon, SortDescIcon } from "./Icons";

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  pagination: PaginationState;
  totalPages: number;
  total: number;
  onPaginationChange: OnChangeFn<PaginationState>;
  sorting?: SortingState;
  onSortingChange?: OnChangeFn<SortingState>;
  isLoading?: boolean;
  error?: Error | null;
  onRowClick?: (row: T) => void;
  emptyIcon?: string;
  emptyText?: string;
}

export default function DataTable<T extends { id: number }>({
  columns,
  data,
  pagination,
  totalPages,
  total,
  onPaginationChange,
  sorting,
  onSortingChange,
  isLoading,
  error,
  onRowClick,
  emptyIcon = "📋",
  emptyText = "Belum ada data.",
}: DataTableProps<T>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    enableSorting: true,
    enableMultiSort: false,
    pageCount: totalPages,
    state: { pagination, sorting: sorting ?? [] },
    onPaginationChange,
    onSortingChange: onSortingChange ?? (() => {}),
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="skeleton mb-3 h-5 w-full" />
        <div className="skeleton mb-3 h-5 w-3/4" />
        <div className="skeleton h-5 w-5/6" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <span className="empty-state-icon">⚠️</span>
        <p className="empty-state-text">Gagal memuat data.</p>
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="empty-state">
        <span className="empty-state-icon">{emptyIcon}</span>
        <p className="empty-state-text">{emptyText}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="table-plan">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={
                      header.column.getCanSort()
                        ? header.column.getToggleSortingHandler()
                        : undefined
                    }
                    className={
                      header.column.getCanSort()
                        ? "cursor-pointer select-none hover:bg-navy-50/50"
                        : ""
                    }
                  >
                    <span className="inline-flex items-center gap-1">
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                      {{
                        asc: <SortAscIcon />,
                        desc: <SortDescIcon />,
                      }[header.column.getIsSorted() as string] ?? null}
                    </span>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => onRowClick?.(row.original)}
                className={onRowClick ? "cursor-pointer transition-colors hover:bg-surface-hover" : ""}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination footer */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-navy-100/50 px-4 py-3">
        <div className="flex items-center gap-3">
          <p className="text-sm text-ink-muted">
            Menampilkan {data.length} dari {total} data
          </p>
          <div className="h-4 w-px bg-navy-200/50" />
          <label className="flex items-center gap-1.5 text-xs text-ink-muted">
            Baris per halaman
            <select
              value={pagination.pageSize}
              onChange={(e) =>
                onPaginationChange({
                  pageIndex: 0,
                  pageSize: Number(e.target.value),
                })
              }
              className="rounded-plan border border-navy-200/60 bg-surface py-1 pl-2 pr-6 text-xs font-medium text-ink transition-colors hover:border-teal-300 focus:border-teal-400 focus:outline-none focus:ring-1 focus:ring-teal-300"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() =>
              onPaginationChange({ ...pagination, pageIndex: pagination.pageIndex - 1 })
            }
            disabled={!table.getCanPreviousPage()}
            className="btn-ghost flex items-center gap-1 text-xs disabled:opacity-40"
          >
            <ChevronLeftIcon />
            Sebelumnya
          </button>

          {/* Page numbers */}
          <div className="flex items-center gap-1">
            {generatePageNumbers(pagination.pageIndex, totalPages).map((p, i) =>
              p === "..." ? (
                <span key={`ellipsis-${i}`} className="px-1 text-xs text-ink-subtle">
                  ...
                </span>
              ) : (
                <button
                  key={p}
                  onClick={() =>
                    onPaginationChange({ ...pagination, pageIndex: p as number })
                  }
                  className={`flex h-7 w-7 items-center justify-center rounded-plan text-xs font-medium transition-colors ${
                    p === pagination.pageIndex
                      ? "bg-teal-500 text-white"
                      : "text-ink-muted hover:bg-navy-100/50"
                  }`}
                >
                  {(p as number) + 1}
                </button>
              ),
            )}
          </div>

          <button
            onClick={() =>
              onPaginationChange({ ...pagination, pageIndex: pagination.pageIndex + 1 })
            }
            disabled={!table.getCanNextPage()}
            className="btn-ghost flex items-center gap-1 text-xs disabled:opacity-40"
          >
            Selanjutnya
            <ChevronRightIcon />
          </button>
        </div>
      </div>
    </div>
  );
}

function generatePageNumbers(
  current: number,
  total: number,
): (number | "..." )[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i);
  }

  const pages: (number | "...")[] = [];

  if (current <= 3) {
    for (let i = 0; i < 5; i++) pages.push(i);
    pages.push("...");
    pages.push(total - 1);
  } else if (current >= total - 4) {
    pages.push(0);
    pages.push("...");
    for (let i = total - 5; i < total; i++) pages.push(i);
  } else {
    pages.push(0);
    pages.push("...");
    for (let i = current - 1; i <= current + 1; i++) pages.push(i);
    pages.push("...");
    pages.push(total - 1);
  }

  return pages;
}

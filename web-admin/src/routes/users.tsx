import { useState, useCallback } from "react";
import { createRoute } from "@tanstack/react-router";
import type { PaginationState, SortingState, ColumnDef, OnChangeFn } from "@tanstack/react-table";
import { protectedRoute } from "./_protected";
import Modal from "../components/Modal";
import DataTable from "../components/DataTable";
import { useDebounce } from "../hooks/useDebounce";
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useAdminResetPassword,
  useUserRooms,
  useAssignUserToRoom,
  useUnassignUserFromRoom,
  type User,
  ROLES,
} from "../hooks/useUsers";
import { useRoomsAll } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/users",
  component: UsersPage,
});

const ROLE_LABELS: Record<string, string> = {
  admin_ppi: "Admin PPI",
  supervisor: "Supervisor",
  inspector: "Inspector",
};

function UsersPage() {
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  });
  const [sorting, setSorting] = useState<SortingState>([]);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const activeSort = sorting[0];
  const sortBy = activeSort?.id;
  const sortOrder = activeSort?.desc ? "desc" : "asc";
  const { data: result, isLoading, error } = useUsers(
    pagination.pageIndex,
    pagination.pageSize,
    debouncedSearch,
    sortBy,
    sortOrder,
  );

  const handleSortingChange: OnChangeFn<SortingState> = (updater) => {
    setSorting(updater);
    setPagination((p) => ({ ...p, pageIndex: 0 }));
  };
  const create = useCreateUser();
  const update = useUpdateUser();
  const del = useDeleteUser();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [resetPwUser, setResetPwUser] = useState<User | null>(null);
  const [roomAssignUser, setRoomAssignUser] = useState<User | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("inspector");
  const [editActive, setEditActive] = useState(true);
  const [saveError, setSaveError] = useState("");

  const openCreate = () => {
    setEditing(null);
    setUsername("");
    setPassword("");
    setRole("inspector");
    setEditActive(true);
    setSaveError("");
    setModalOpen(true);
  };

  const openEdit = (u: User) => {
    setEditing(u);
    setUsername(u.username);
    setPassword("");
    setRole(u.role);
    setEditActive(u.is_active);
    setSaveError("");
    setModalOpen(true);
  };

  const handleSave = async () => {
    const trimmed = username.trim();
    if (!trimmed) return;
    setSaveError("");
    try {
      if (editing) {
        await update.mutateAsync({
          id: editing.id,
          username: trimmed,
          role,
          is_active: editActive,
        });
      } else {
        if (!password) {
          setSaveError("Password harus diisi untuk pengguna baru");
          return;
        }
        await create.mutateAsync({ username: trimmed, password, role });
      }
      setModalOpen(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Gagal menyimpan");
    }
  };

  const columns: ColumnDef<User>[] = [
    {
      accessorKey: "username",
      header: "Username",
      cell: ({ row }) => (
        <span className="font-medium text-ink">{row.original.username}</span>
      ),
    },
    {
      accessorKey: "role",
      header: "Role",
      cell: ({ row }) => (
        <span className="inline-flex items-center rounded-full bg-navy-100/40 px-2.5 py-0.5 text-xs font-medium text-navy-600 ring-1 ring-inset ring-navy-200/50">
          {ROLE_LABELS[row.original.role] ?? row.original.role}
        </span>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) =>
        row.original.is_active ? (
          <span className="badge-approved">Aktif</span>
        ) : (
          <span className="inline-flex items-center rounded-full bg-navy-100/40 px-2.5 py-0.5 text-xs font-medium text-navy-500 ring-1 ring-inset ring-navy-200/50">
            Nonaktif
          </span>
        ),
    },
    {
      id: "actions",
      header: () => <span className="text-right block">Aksi</span>,
      cell: ({ row }) => {
        const u = row.original;
        return (
          <div className="text-right">
            {u.role !== "admin_ppi" && (
              <button
                onClick={() => setRoomAssignUser(u)}
                className="btn-ghost text-xs"
              >
                Ruangan
              </button>
            )}
            <button onClick={() => openEdit(u)} className="btn-ghost text-xs">
              Edit
            </button>
            <button
              onClick={() => setResetPwUser(u)}
              className="btn-ghost text-xs text-ink-muted hover:text-teal-600"
            >
              Reset PW
            </button>
            <button
              onClick={() => {
                if (window.confirm(`Nonaktifkan pengguna "${u.username}"?`)) {
                  del.mutate(u.id);
                }
              }}
              className="btn-ghost text-xs text-ink-muted hover:text-danger"
            >
              Hapus
            </button>
          </div>
        );
      },
    },
  ];

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Pengguna</h1>
          <p className="page-subtitle">Kelola akun inspector, supervisor, dan admin</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          + Tambah Pengguna
        </button>
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
            placeholder="Cari pengguna..."
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
          emptyIcon="👤"
          emptyText={search ? "Tidak ada hasil." : "Belum ada pengguna."}
        />
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Edit Pengguna" : "Tambah Pengguna"}
      >
        <div className="mb-4">
          <label className="label-plan">Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input-plan"
            placeholder="Masukkan username"
            autoFocus
          />
        </div>

        {!editing && (
          <div className="mb-4">
            <label className="label-plan">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-plan"
              placeholder="Masukkan password"
            />
          </div>
        )}

        {editing && (
          <div className="mb-4">
            <label className="label-plan">Aktif</label>
            <label className="flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                checked={editActive}
                onChange={(e) => setEditActive(e.target.checked)}
                className="h-4 w-4 rounded border-navy-300 text-teal-600 focus:ring-teal-500"
              />
              Pengguna aktif
            </label>
          </div>
        )}

        <div className="mb-4">
          <label className="label-plan">Role</label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="input-plan"
          >
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </div>

        {editing && (
          <p className="mb-2 text-xs text-ink-subtle">
            Biarkan password kosong untuk tidak mengubah password.
          </p>
        )}

        {saveError && (
          <p className="mt-2 animate-fade-in text-sm text-danger">{saveError}</p>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <button onClick={() => setModalOpen(false)} className="btn-secondary">
            Batal
          </button>
          <button
            onClick={handleSave}
            disabled={!username.trim() || create.isPending || update.isPending}
            className="btn-primary"
          >
            {create.isPending || update.isPending ? "Menyimpan..." : "Simpan"}
          </button>
        </div>
      </Modal>

      {/* ═══ Reset Password Modal ═══ */}
      <ResetPasswordModal
        user={resetPwUser}
        onClose={() => setResetPwUser(null)}
      />

      {/* ═══ Room Assignment Modal ═══ */}
      <UserRoomModal
        user={roomAssignUser}
        onClose={() => setRoomAssignUser(null)}
      />
    </div>
  );
}

function UserRoomModal({
  user,
  onClose,
}: {
  user: User | null;
  onClose: () => void;
}) {
  const { data: allRooms } = useRoomsAll();
  const { data: userRooms } = useUserRooms(user?.id ?? 0);
  const assignRoom = useAssignUserToRoom();
  const unassignRoom = useUnassignUserFromRoom();

  const assignedRoomIds = new Set(userRooms?.map((ur) => ur.room_id) ?? []);

  const handleToggle = async (roomId: number) => {
    if (!user) return;
    if (assignedRoomIds.has(roomId)) {
      await unassignRoom.mutateAsync({ userId: user.id, roomId });
    } else {
      await assignRoom.mutateAsync({ userId: user.id, roomId });
    }
  };

  if (!user) return null;

  return (
    <Modal
      open={!!user}
      onClose={onClose}
      title={`Ruangan — ${user.username}`}
    >
      <p className="mb-4 text-sm text-ink-muted">
        Centang ruangan yang menjadi tanggung jawab pengguna ini.
      </p>
      <div className="max-h-80 space-y-2 overflow-y-auto">
        {allRooms?.map((room) => (
          <label
            key={room.id}
            className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-navy-50"
          >
            <input
              type="checkbox"
              checked={assignedRoomIds.has(room.id)}
              onChange={() => handleToggle(room.id)}
              className="h-4 w-4 rounded border-navy-300 text-teal-600 focus:ring-teal-500"
            />
            <span className="text-sm text-ink">{room.name}</span>
          </label>
        ))}
        {!allRooms?.length && (
          <p className="py-8 text-center text-sm text-ink-subtle">
            Belum ada ruangan.
          </p>
        )}
      </div>
    </Modal>
  );
}

function generatePassword(): string {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  const array = new Uint8Array(12);
  crypto.getRandomValues(array);
  let result = "";
  for (let i = 0; i < 12; i++) {
    result += chars[array[i] % chars.length];
  }
  return result;
}

function ResetPasswordModal({
  user,
  onClose,
}: {
  user: User | null;
  onClose: () => void;
}) {
  const resetPw = useAdminResetPassword();
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSave = useCallback(async () => {
    if (!user) return;
    setError("");
    setSuccess(false);

    if (!newPw) {
      setError("Password baru harus diisi");
      return;
    }
    if (newPw.length < 6) {
      setError("Password minimal 6 karakter");
      return;
    }
    if (newPw !== confirmPw) {
      setError("Password tidak cocok");
      return;
    }

    try {
      await resetPw.mutateAsync({ user_id: user.id, new_password: newPw });
      setSuccess(true);
      setNewPw("");
      setConfirmPw("");
      setTimeout(() => onClose(), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mereset password");
    }
  }, [user, newPw, confirmPw, resetPw, onClose]);

  const handleGenerate = useCallback(() => {
    const pw = generatePassword();
    setNewPw(pw);
    setConfirmPw(pw);
    setError("");
    setSuccess(false);
  }, []);

  if (!user) return null;

  return (
    <Modal
      open={!!user}
      onClose={onClose}
      title={`Reset Password - ${user.username}`}
    >
      <div className="mb-4">
        <label className="label-plan">Password Baru</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={newPw}
            onChange={(e) => {
              setNewPw(e.target.value);
              setError("");
              setSuccess(false);
            }}
            className="input-plan flex-1"
            placeholder="Masukkan password baru atau generate"
            autoFocus
          />
          <button
            onClick={handleGenerate}
            className="btn-ghost shrink-0 text-xs text-teal-600 hover:text-teal-700"
            title="Generate password acak"
          >
            Generate
          </button>
        </div>
      </div>

      <div className="mb-4">
        <label className="label-plan">Konfirmasi Password Baru</label>
        <input
          type="text"
          value={confirmPw}
          onChange={(e) => {
            setConfirmPw(e.target.value);
            setError("");
            setSuccess(false);
          }}
          className="input-plan"
          placeholder="Ulangi password baru"
        />
      </div>

      <p className="mb-2 text-xs text-ink-subtle">
        Password akan langsung direset. Beri tahu user password barunya.
      </p>

      {error && (
        <p className="animate-fade-in text-sm text-danger">{error}</p>
      )}
      {success && (
        <p className="animate-fade-in text-sm text-success">Password berhasil direset!</p>
      )}

      <div className="mt-6 flex justify-end gap-3">
        <button onClick={onClose} className="btn-secondary">Batal</button>
        <button
          onClick={handleSave}
          disabled={resetPw.isPending}
          className="btn-primary"
        >
          {resetPw.isPending ? "Menyimpan..." : "Simpan"}
        </button>
      </div>
    </Modal>
  );
}

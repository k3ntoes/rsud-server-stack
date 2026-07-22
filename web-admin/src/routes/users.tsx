import { useState, useCallback } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import Modal from "../components/Modal";
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useAdminResetPassword,
  type User,
  ROLES,
} from "../hooks/useUsers";

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
  const { data: users, isLoading, error } = useUsers();
  const create = useCreateUser();
  const update = useUpdateUser();
  const del = useDeleteUser();

  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [resetPwUser, setResetPwUser] = useState<User | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("inspector");
  const [saveError, setSaveError] = useState("");

  const openCreate = () => {
    setEditing(null);
    setUsername("");
    setPassword("");
    setRole("inspector");
    setSaveError("");
    setModalOpen(true);
  };

  const openEdit = (u: User) => {
    setEditing(u);
    setUsername(u.username);
    setPassword("");
    setRole(u.role);
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
          is_active: editing.is_active,
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

  const filtered = users?.filter((u) =>
    u.username.toLowerCase().includes(search.toLowerCase()),
  );

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
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cari pengguna..."
            className="input-plan max-w-xs"
          />
        </div>

        {isLoading ? (
          <div className="p-8">
            <div className="skeleton mb-3 h-5 w-3/4" />
            <div className="skeleton mb-3 h-5 w-1/2" />
            <div className="skeleton h-5 w-2/3" />
          </div>
        ) : error ? (
          <div className="empty-state">
            <span className="empty-state-icon">⚠️</span>
            <p className="empty-state-text">Gagal memuat data.</p>
          </div>
        ) : filtered?.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">👤</span>
            <p className="empty-state-text">
              {search ? "Tidak ada hasil." : "Belum ada pengguna."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-plan">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th className="text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {filtered?.map((u) => (
                  <tr key={u.id}>
                    <td className="font-medium text-ink">{u.username}</td>
                    <td>
                      <span className="inline-flex items-center rounded-full bg-navy-100/40 px-2.5 py-0.5 text-xs font-medium text-navy-600 ring-1 ring-inset ring-navy-200/50">
                        {ROLE_LABELS[u.role] ?? u.role}
                      </span>
                    </td>
                    <td>
                      {u.is_active ? (
                        <span className="badge-approved">Aktif</span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-navy-100/40 px-2.5 py-0.5 text-xs font-medium text-navy-500 ring-1 ring-inset ring-navy-200/50">
                          Nonaktif
                        </span>
                      )}
                    </td>
                    <td className="text-right">
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
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
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
                checked={editing.is_active}
                onChange={(e) =>
                  setEditing({ ...editing, is_active: e.target.checked })
                }
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
    </div>
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

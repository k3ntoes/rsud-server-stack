import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import MasterDataPage from "../components/MasterDataPage";
import {
  useRooms,
  useCreateRoom,
  useUpdateRoom,
  useDeleteRoom,
  type Room,
} from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/rooms",
  component: () => (
    <MasterDataPage<Room>
      title="Ruangan"
      subtitle="Kelola daftar ruangan untuk inspeksi kebersihan"
      addLabel="Tambah Ruangan"
      searchPlaceholder="Cari ruangan..."
      entityLabel="Nama Ruangan"
      inputPlaceholder="Masukkan nama ruangan"
      modalEditTitle="Edit Ruangan"
      modalAddTitle="Tambah Ruangan"
      emptyIcon="🏥"
      emptyText="Belum ada ruangan. Klik 'Tambah Ruangan' untuk memulai."
      useList={useRooms}
      useCreate={useCreateRoom}
      useUpdate={useUpdateRoom}
      useDelete={useDeleteRoom}
    />
  ),
});

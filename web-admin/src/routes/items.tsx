import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import MasterDataPage from "../components/MasterDataPage";
import {
  useItems,
  useCreateItem,
  useUpdateItem,
  useDeleteItem,
  type Item,
} from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/items",
  component: () => (
    <MasterDataPage<Item>
      title="Item Inspeksi"
      subtitle="Kelola item yang dinilai dalam inspeksi kebersihan"
      addLabel="Tambah Item"
      searchPlaceholder="Cari item..."
      entityLabel="Nama Item"
      inputPlaceholder="Masukkan nama item"
      modalEditTitle="Edit Item Inspeksi"
      modalAddTitle="Tambah Item Inspeksi"
      emptyIcon="📋"
      emptyText="Belum ada item. Klik 'Tambah Item' untuk memulai."
      useList={useItems}
      useCreate={useCreateItem}
      useUpdate={useUpdateItem}
      useDelete={useDeleteItem}
    />
  ),
});

import { useEffect, useRef, type ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

export default function Modal({ open, onClose, title, children }: ModalProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    else if (!open && el.open) el.close();
  }, [open]);

  // Close on backdrop click
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const handler = (e: MouseEvent) => {
      if (e.target === el) onClose();
    };
    el.addEventListener("click", handler);
    return () => el.removeEventListener("click", handler);
  }, [onClose]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-0 shadow-2xl backdrop:bg-black/40"
    >
      <div className="flex items-center justify-between border-b px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        <button
          onClick={onClose}
          className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          aria-label="Close"
        >
          <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
          </svg>
        </button>
      </div>
      <div className="px-6 py-4">{children}</div>
    </dialog>
  );
}

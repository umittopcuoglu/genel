'use client';

import { useEffect, useRef, ReactNode } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const SIZE_CLASSES = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-2xl',
};

export function Modal({ open, onClose, title, children, size = 'md' }: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      // Save current focus
      previousFocus.current = document.activeElement as HTMLElement;

      // ESC key closes modal
      const handleEsc = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
      };

      // Trap focus inside modal
      const handleTab = (e: KeyboardEvent) => {
        if (e.key !== 'Tab' || !modalRef.current) return;
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      };

      window.addEventListener('keydown', handleEsc);
      window.addEventListener('keydown', handleTab);

      // Lock body scroll
      document.body.style.overflow = 'hidden';

      // Focus first focusable element
      setTimeout(() => {
        const firstFocusable = modalRef.current?.querySelector<HTMLElement>(
          'input, select, textarea, button'
        );
        firstFocusable?.focus();
      }, 50);

      return () => {
        window.removeEventListener('keydown', handleEsc);
        window.removeEventListener('keydown', handleTab);
        document.body.style.overflow = '';
        // Restore focus
        previousFocus.current?.focus();
      };
    }
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          ref={modalRef}
          className={`w-full ${SIZE_CLASSES[size]} rounded-lg bg-surface border border-line shadow-xl`}
          onClick={(e) => e.stopPropagation()}
        >
        <div className="flex items-center justify-between border-b border-line p-4">
          <h2 id="modal-title" className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-text-2 hover:bg-bg hover:text-text-1 focus:outline-none focus:ring-2 focus:ring-accent/60"
            aria-label="Kapat"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        {children}
        </div>
      </div>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose: () => void;
}

const TYPE_STYLES: Record<ToastType, { bg: string; border: string; text: string; icon: any }> = {
  success: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    border: 'border-emerald-200 dark:border-emerald-800',
    text: 'text-emerald-800 dark:text-emerald-200',
    icon: CheckCircle,
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-950/30',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-800 dark:text-red-200',
    icon: AlertCircle,
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-950/30',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-800 dark:text-blue-200',
    icon: Info,
  },
  warning: {
    bg: 'bg-amber-50 dark:bg-amber-950/30',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-800 dark:text-amber-200',
    icon: AlertTriangle,
  },
};

export function Toast({ message, type = 'info', duration = 4000, onClose }: ToastProps) {
  const [visible, setVisible] = useState(true);
  const style = TYPE_STYLES[type];
  const Icon = style.icon;

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onClose, 300);
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`pointer-events-auto flex items-start gap-3 rounded-lg border ${style.bg} ${style.border} ${style.text} p-4 shadow-lg transition-all duration-300 ${
        visible ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'
      }`}
    >
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      <p className="flex-1 text-sm font-medium">{message}</p>
      <button
        onClick={() => {
          setVisible(false);
          setTimeout(onClose, 300);
        }}
        className="rounded-md p-0.5 hover:bg-black/10 dark:hover:bg-white/10"
        aria-label="Kapat"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

// Toast Manager Hook
let toastIdCounter = 0;
const toastListeners: ((toasts: ToastItem[]) => void)[] = [];
let toastQueue: ToastItem[] = [];

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
  duration?: number;
}

export const toast = {
  show(message: string, type: ToastType = 'info', duration = 4000) {
    const newToast: ToastItem = {
      id: ++toastIdCounter,
      message,
      type,
      duration,
    };
    toastQueue = [...toastQueue, newToast];
    toastListeners.forEach((listener) => listener(toastQueue));
  },
  success(message: string, duration?: number) {
    this.show(message, 'success', duration);
  },
  error(message: string, duration?: number) {
    this.show(message, 'error', duration);
  },
  info(message: string, duration?: number) {
    this.show(message, 'info', duration);
  },
  warning(message: string, duration?: number) {
    this.show(message, 'warning', duration);
  },
};

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    toastListeners.push(setToasts);
    return () => {
      const idx = toastListeners.indexOf(setToasts);
      if (idx > -1) toastListeners.splice(idx, 1);
    };
  }, []);

  const removeToast = (id: number) => {
    toastQueue = toastQueue.filter((t) => t.id !== id);
    setToasts(toastQueue);
  };

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="pointer-events-none fixed top-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
    >
      {toasts.map((t) => (
        <Toast
          key={t.id}
          message={t.message}
          type={t.type}
          duration={t.duration}
          onClose={() => removeToast(t.id)}
        />
      ))}
    </div>
  );
}

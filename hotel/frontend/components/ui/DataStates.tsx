'use client';

import { Loader2, Inbox, AlertCircle, RefreshCw } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = 'Yükleniyor...' }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20" role="status" aria-live="polite">
      <Loader2 className="h-8 w-8 animate-spin text-accent" />
      <p className="mt-3 text-sm text-text-2">{message}</p>
    </div>
  );
}

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

export function EmptyState({
  title = 'Henüz veri yok',
  description = 'Burada gösterilecek kayıt bulunamadı.',
  action,
  icon,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center" role="status">
      <div className="rounded-full bg-bg p-4">
        {icon || <Inbox className="h-8 w-8 text-text-3" aria-hidden />}
      </div>
      <h3 className="mt-4 text-base font-semibold text-text-1">{title}</h3>
      <p className="mt-1 text-sm text-text-2 max-w-md">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  message = 'Bir hata oluştu',
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      role="alert"
    >
      <div className="rounded-full bg-red-50 dark:bg-red-950/30 p-4">
        <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" aria-hidden />
      </div>
      <h3 className="mt-4 text-base font-semibold text-text-1">Hata</h3>
      <p className="mt-1 text-sm text-text-2 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden /> Tekrar Dene
        </button>
      )}
    </div>
  );
}

interface MockBannerProps {
  message?: string;
}

export function MockBanner({
  message = "Demo veri gösteriliyor — backend bağlandığında gerçek veriler yüklenecek",
}: MockBannerProps) {
  return (
    <div
      role="status"
      className="rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 px-4 py-2 text-xs text-amber-800 dark:text-amber-200"
    >
      ⚠️ {message}
    </div>
  );
}

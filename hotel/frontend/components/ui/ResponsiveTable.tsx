'use client';

import React from 'react';

interface ResponsiveTableProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Wraps a table for responsive display:
 * - Desktop: horizontal table
 * - Mobile: stacked cards (with data-label attribute on td for label)
 */
export function ResponsiveTable({ children, className = '' }: ResponsiveTableProps) {
  return (
    <div className={`responsive-table-wrapper ${className}`}>
      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="responsive-table w-full text-sm">{children}</table>
      </div>
    </div>
  );
}

/**
 * Mobile-friendly card grid replacement for tables.
 * Use this when you want a different layout on mobile.
 */
interface MobileCardListProps<T> {
  items: T[];
  renderCard: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
}

export function MobileCardList<T>({
  items,
  renderCard,
  keyExtractor,
  emptyMessage = 'Veri yok',
}: MobileCardListProps<T>) {
  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line p-8 text-center text-sm text-text-2">
        {emptyMessage}
      </div>
    );
  }
  return (
    <div className="space-y-2 md:hidden">
      {items.map((item) => (
        <div key={keyExtractor(item)} className="rounded-lg border border-line bg-surface p-3">
          {renderCard(item)}
        </div>
      ))}
    </div>
  );
}

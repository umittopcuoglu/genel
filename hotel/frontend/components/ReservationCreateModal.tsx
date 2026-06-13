'use client';

import { useState } from 'react';
import { X } from 'lucide-react';

interface ReservationCreateModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function ReservationCreateModal({ open, onClose, onSuccess }: ReservationCreateModalProps) {
  const [formData, setFormData] = useState({
    guest_name: '',
    guest_email: '',
    guest_phone: '',
    check_in: '',
    check_out: '',
    adults: 2,
    children: 0,
    room_type: 'standard',
    source: 'direct',
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validation
      if (new Date(formData.check_out) <= new Date(formData.check_in)) {
        throw new Error('Çıkış tarihi giriş tarihinden sonra olmalı');
      }

      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const response = await fetch('/api/v1/reservations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error?.message || data.detail || 'Rezervasyon oluşturulamadı');
      }

      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
      <div className="w-full max-w-2xl rounded-lg bg-surface border border-line shadow-xl my-8">
        <div className="flex items-center justify-between border-b border-line p-4">
          <h2 className="text-lg font-semibold">Yeni Rezervasyon</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-text-2 hover:bg-bg hover:text-text-1"
            aria-label="Kapat"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-text-1 mb-1">Misafir Adı *</label>
              <input
                type="text"
                required
                value={formData.guest_name}
                onChange={(e) => setFormData({ ...formData, guest_name: e.target.value })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/20"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-1 mb-1">E-posta</label>
              <input
                type="email"
                value={formData.guest_email}
                onChange={(e) => setFormData({ ...formData, guest_email: e.target.value })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-1 mb-1">Telefon</label>
              <input
                type="tel"
                value={formData.guest_phone}
                onChange={(e) => setFormData({ ...formData, guest_phone: e.target.value })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-1 mb-1">Kaynak</label>
              <select
                value={formData.source}
                onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
              >
                <option value="direct">Direkt</option>
                <option value="ota">OTA</option>
                <option value="walkin">Walk-in</option>
                <option value="phone">Telefon</option>
                <option value="corporate">Kurumsal</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-1 mb-1">Giriş Tarihi *</label>
              <input
                type="date"
                required
                value={formData.check_in}
                onChange={(e) => setFormData({ ...formData, check_in: e.target.value })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-1 mb-1">Çıkış Tarihi *</label>
              <input
                type="date"
                required
                value={formData.check_out}
                onChange={(e) => setFormData({ ...formData, check_out: e.target.value })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-1 mb-1">Yetişkin</label>
              <input
                type="number"
                min={1}
                max={6}
                value={formData.adults}
                onChange={(e) => setFormData({ ...formData, adults: parseInt(e.target.value) })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-1 mb-1">Çocuk</label>
              <input
                type="number"
                min={0}
                max={4}
                value={formData.children}
                onChange={(e) => setFormData({ ...formData, children: parseInt(e.target.value) })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-1 mb-1">Oda Tipi</label>
              <select
                value={formData.room_type}
                onChange={(e) => setFormData({ ...formData, room_type: e.target.value })}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
              >
                <option value="standard">Standart</option>
                <option value="deluxe">Deluxe</option>
                <option value="suite">Suite</option>
                <option value="family">Aile</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-1 mb-1">Notlar</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
                placeholder="Özel istekler, bilgiler..."
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-line">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-text-1 hover:bg-bg"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
            >
              {loading ? 'Oluşturuluyor...' : 'Rezervasyon Oluştur'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

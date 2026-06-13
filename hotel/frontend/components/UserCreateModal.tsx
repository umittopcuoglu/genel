'use client';

import { useState } from 'react';
import { X } from 'lucide-react';

interface UserCreateModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const ROLES = [
  { value: 'superadmin', label: 'Süper Admin' },
  { value: 'manager', label: 'Müdür' },
  { value: 'frontdesk', label: 'Ön Büro' },
  { value: 'housekeeping', label: 'Kat Hizmetleri' },
  { value: 'accounting', label: 'Muhasebe' },
  { value: 'maintenance', label: 'Bakım' },
  { value: 'fb', label: 'F&B' },
  { value: 'hr', label: 'İK' },
];

export function UserCreateModal({ open, onClose, onSuccess }: UserCreateModalProps) {
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'frontdesk',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const response = await fetch('/api/v1/auth/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error?.message || data.detail || 'Kullanıcı oluşturulamadı');
      }

      onSuccess?.();
      setFormData({ email: '', full_name: '', password: '', role: 'frontdesk' });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg bg-surface border border-line shadow-xl">
        <div className="flex items-center justify-between border-b border-line p-4">
          <h2 className="text-lg font-semibold">Yeni Kullanıcı Oluştur</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-text-2 hover:bg-bg hover:text-text-1"
            aria-label="Kapat"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-4">
          <div>
            <label className="block text-sm font-medium text-text-1 mb-1">Ad Soyad</label>
            <input
              type="text"
              required
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/20"
              placeholder="Ahmet Yılmaz"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-1 mb-1">E-posta</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/20"
              placeholder="kullanici@hotel.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-1 mb-1">Şifre</label>
            <input
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/20"
              placeholder="En az 8 karakter"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-1 mb-1">Rol</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60"
            >
              {ROLES.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
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
              {loading ? 'Oluşturuluyor...' : 'Oluştur'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

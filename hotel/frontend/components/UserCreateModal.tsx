'use client';

import { useState } from 'react';
import { FormField, Input, PasswordInput, Select } from '@/components/ui/FormField';
import { toast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';

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

interface FormErrors {
  email?: string;
  full_name?: string;
  password?: string;
  password_confirm?: string;
}

export function UserCreateModal({ open, onClose, onSuccess }: UserCreateModalProps) {
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    password_confirm: '',
    role: 'frontdesk',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);

  const validateField = (name: string, value: string): string | undefined => {
    switch (name) {
      case 'email':
        if (!value) return 'E-posta gereklidir';
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Geçerli bir e-posta girin';
        return undefined;
      case 'full_name':
        if (!value) return 'Ad soyad gereklidir';
        if (value.length < 2) return 'Ad soyad çok kısa';
        return undefined;
      case 'password':
        if (!value) return 'Şifre gereklidir';
        if (value.length < 8) return 'En az 8 karakter';
        if (!/[A-Z]/.test(value)) return 'En az bir büyük harf içermeli';
        if (!/\d/.test(value)) return 'En az bir rakam içermeli';
        return undefined;
      case 'password_confirm':
        if (!value) return 'Şifreyi tekrar girin';
        if (value !== formData.password) return 'Şifreler eşleşmiyor';
        return undefined;
    }
    return undefined;
  };

  const handleBlur = (name: string) => {
    setTouched({ ...touched, [name]: true });
    setErrors({ ...errors, [name]: validateField(name, formData[name as keyof typeof formData] as string) });
  };

  const handleChange = (name: string, value: string) => {
    setFormData({ ...formData, [name]: value });
    if (touched[name]) {
      setErrors({ ...errors, [name]: validateField(name, value) });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all
    const newErrors: FormErrors = {};
    ['email', 'full_name', 'password', 'password_confirm'].forEach((field) => {
      const error = validateField(field, formData[field as keyof typeof formData] as string);
      if (error) newErrors[field as keyof FormErrors] = error;
    });
    setErrors(newErrors);
    setTouched({ email: true, full_name: true, password: true, password_confirm: true });

    if (Object.keys(newErrors).length > 0) return;

    setLoading(true);
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const response = await fetch('/api/v1/auth/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          email: formData.email,
          full_name: formData.full_name,
          password: formData.password,
          role: formData.role,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error?.message || data.detail || 'Kullanıcı oluşturulamadı');
      }

      toast.success('Kullanıcı başarıyla oluşturuldu');
      onSuccess?.();
      setFormData({ email: '', full_name: '', password: '', password_confirm: '', role: 'frontdesk' });
      setTouched({});
      setErrors({});
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Bilinmeyen hata');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Yeni Kullanıcı Oluştur" size="md">
        <form onSubmit={handleSubmit} className="space-y-4 p-4" noValidate>
          <FormField label="Ad Soyad" required error={touched.full_name ? errors.full_name : undefined}>
            <Input
              type="text"
              value={formData.full_name}
              onChange={(e) => handleChange('full_name', e.target.value)}
              onBlur={() => handleBlur('full_name')}
              error={touched.full_name && !!errors.full_name}
              placeholder="Ahmet Yılmaz"
              autoComplete="name"
            />
          </FormField>

          <FormField label="E-posta" required error={touched.email ? errors.email : undefined}>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              onBlur={() => handleBlur('email')}
              error={touched.email && !!errors.email}
              placeholder="kullanici@hotel.com"
              autoComplete="email"
            />
          </FormField>

          <FormField
            label="Şifre"
            required
            error={touched.password ? errors.password : undefined}
            hint="En az 8 karakter, 1 büyük harf, 1 rakam"
          >
            <PasswordInput
              value={formData.password}
              onChange={(e) => handleChange('password', e.target.value)}
              onBlur={() => handleBlur('password')}
              error={touched.password && !!errors.password}
              showStrength
              autoComplete="new-password"
            />
          </FormField>

          <FormField
            label="Şifre Tekrar"
            required
            error={touched.password_confirm ? errors.password_confirm : undefined}
          >
            <PasswordInput
              value={formData.password_confirm}
              onChange={(e) => handleChange('password_confirm', e.target.value)}
              onBlur={() => handleBlur('password_confirm')}
              error={touched.password_confirm && !!errors.password_confirm}
              autoComplete="new-password"
            />
          </FormField>

          <FormField label="Rol">
            <Select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            >
              {ROLES.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </Select>
          </FormField>

          <div className="flex justify-end gap-2 pt-2 border-t border-line">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-text-1 hover:bg-bg disabled:opacity-50"
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
    </Modal>
  );
}

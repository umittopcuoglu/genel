'use client';

import { useState, ReactNode } from 'react';
import { AlertCircle, Check, Eye, EyeOff } from 'lucide-react';

interface FormFieldProps {
  label: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: ReactNode;
}

export function FormField({ label, required, error, hint, children }: FormFieldProps) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-text-1">
        {label}
        {required && <span className="ml-1 text-red-600 dark:text-red-400">*</span>}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-text-2">{hint}</p>}
      {error && (
        <p className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
          <AlertCircle className="h-3 w-3" aria-hidden />
          {error}
        </p>
      )}
    </div>
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export function Input({ error, className = '', ...props }: InputProps) {
  return (
    <input
      {...props}
      className={`w-full rounded-lg border bg-bg px-3 py-2 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent/20 ${
        error
          ? 'border-red-500 dark:border-red-400 focus:border-red-500'
          : 'border-line focus:border-accent/60'
      } ${className}`}
    />
  );
}

interface PasswordInputProps extends Omit<InputProps, 'type'> {
  showStrength?: boolean;
}

export function PasswordInput({ showStrength, value, ...props }: PasswordInputProps) {
  const [show, setShow] = useState(false);
  const strength = showStrength ? calculateStrength(String(value || '')) : null;

  return (
    <div className="space-y-1">
      <div className="relative">
        <Input
          {...props}
          type={show ? 'text' : 'password'}
          value={value}
          className="pr-10"
        />
        <button
          type="button"
          onClick={() => setShow(!show)}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-text-2 hover:text-text-1"
          aria-label={show ? 'Şifreyi gizle' : 'Şifreyi göster'}
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
      {strength && (
        <div className="space-y-1">
          <div className="flex gap-1 h-1">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={`flex-1 rounded-full transition-colors ${
                  i <= strength.score
                    ? strength.score < 2
                      ? 'bg-red-500'
                      : strength.score < 3
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                    : 'bg-line'
                }`}
              />
            ))}
          </div>
          <p className={`text-xs ${
            strength.score < 2
              ? 'text-red-600 dark:text-red-400'
              : strength.score < 3
              ? 'text-amber-600 dark:text-amber-400'
              : 'text-emerald-600 dark:text-emerald-400'
          }`}>
            {strength.label}
          </p>
        </div>
      )}
    </div>
  );
}

function calculateStrength(password: string): { score: number; label: string } {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const labels = ['Çok zayıf', 'Zayıf', 'Orta', 'Güçlü', 'Çok güçlü'];
  return { score, label: labels[score] };
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

export function Select({ error, className = '', children, ...props }: SelectProps) {
  return (
    <select
      {...props}
      className={`w-full rounded-lg border bg-bg px-3 py-2 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent/20 ${
        error
          ? 'border-red-500 dark:border-red-400 focus:border-red-500'
          : 'border-line focus:border-accent/60'
      } ${className}`}
    >
      {children}
    </select>
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export function Textarea({ error, className = '', ...props }: TextareaProps) {
  return (
    <textarea
      {...props}
      className={`w-full rounded-lg border bg-bg px-3 py-2 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent/20 ${
        error
          ? 'border-red-500 dark:border-red-400 focus:border-red-500'
          : 'border-line focus:border-accent/60'
      } ${className}`}
    />
  );
}

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date, opts?: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat('en-IN', opts || { day: '2-digit', month: 'short', year: 'numeric' }).format(
    new Date(date)
  );
}

export function formatDateTime(date: string | Date) {
  return formatDate(date, { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export function truncate(str: string, n = 80) {
  return str.length > n ? str.slice(0, n - 1) + '…' : str;
}

export const RECORD_TYPES = [
  { value: 'prescription', label: 'Prescription' },
  { value: 'lab_result', label: 'Lab Result' },
  { value: 'imaging', label: 'Imaging' },
  { value: 'discharge_summary', label: 'Discharge Summary' },
  { value: 'consultation', label: 'Consultation' },
] as const;

export const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const;

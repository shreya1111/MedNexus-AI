export type UserRole = 'patient' | 'doctor' | 'admin';

export interface User {
  _id: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  role: UserRole;
  avatar?: string;
  isActive: boolean;
  isEmailVerified: boolean;
  lastLogin?: string;
  createdAt: string;
}

export interface PatientProfile {
  _id: string;
  user: string | User;
  dateOfBirth?: string;
  gender?: 'male' | 'female' | 'other';
  bloodType?: string;
  height?: number;
  weight?: number;
  allergies: string[];
  chronicConditions: string[];
  emergencyContact?: { name: string; phone: string; relation: string };
  insurance?: { provider: string; policyNumber: string };
}

export interface MedicalRecord {
  _id: string;
  patient: string | User;
  doctor?: string | User;
  type: 'prescription' | 'lab_result' | 'imaging' | 'discharge_summary' | 'consultation';
  title: string;
  description: string;
  date: string;
  fileUrl?: string;
  tags: string[];
  aiSummary?: string;
  isProcessed: boolean;
  createdAt: string;
}

export interface Appointment {
  _id: string;
  patient: string | User;
  doctor: string | User;
  scheduledAt: string;
  duration: number;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  type: 'in-person' | 'telemedicine';
  reason: string;
  notes?: string;
  meetingLink?: string;
  createdAt: string;
}

export interface AnalyticsData {
  overview: {
    totalPatients: number;
    totalRecords: number;
    totalAppointments: number;
    newUsersLast30Days: number;
  };
  charts: {
    recordsByType: Array<{ _id: string; count: number }>;
    appointmentsByStatus: Array<{ _id: string; count: number }>;
    monthlyRecords: Array<{ _id: { year: number; month: number }; count: number }>;
  };
  upcoming: Appointment[];
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  pagination?: PaginationMeta;
}

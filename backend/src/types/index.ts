import { Request } from 'express';
import { Document, Types } from 'mongoose';
import { IUser } from '../models/User';

export type { IUser };
export type UserRole = 'patient' | 'doctor' | 'admin';

export interface IPatientProfile extends Document {
  user: Types.ObjectId;
  dateOfBirth?: Date;
  gender?: 'male' | 'female' | 'other';
  bloodType?: string;
  height?: number;
  weight?: number;
  allergies: string[];
  chronicConditions: string[];
  emergencyContact?: { name: string; phone: string; relation: string };
  insurance?: { provider: string; policyNumber: string };
}

export interface IMedicalRecord extends Document {
  patient: Types.ObjectId;
  doctor?: Types.ObjectId;
  type: 'prescription' | 'lab_result' | 'imaging' | 'discharge_summary' | 'consultation';
  title: string;
  description: string;
  date: Date;
  fileUrl?: string;
  filePublicId?: string;
  tags: string[];
  aiSummary?: string;
  isProcessed: boolean;
}

export interface IAppointment extends Document {
  patient: Types.ObjectId;
  doctor: Types.ObjectId;
  scheduledAt: Date;
  duration: number;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  type: 'in-person' | 'telemedicine';
  reason: string;
  notes?: string;
  meetingLink?: string;
}

export interface AuthenticatedRequest extends Request {
  user?: IUser;
}

export interface PaginationQuery {
  page?: string;
  limit?: string;
  sort?: string;
  order?: 'asc' | 'desc';
  search?: string;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  error?: string;
}

import { Schema, model } from 'mongoose';
import { IPatientProfile } from '../types';

const patientProfileSchema = new Schema<IPatientProfile>(
  {
    user: { type: Schema.Types.ObjectId, ref: 'User', required: true, unique: true, index: true },
    dateOfBirth: { type: Date },
    gender: { type: String, enum: ['male', 'female', 'other'] },
    bloodType: { type: String, enum: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] },
    height: { type: Number, min: 0, max: 300 },
    weight: { type: Number, min: 0, max: 500 },
    allergies: [{ type: String }],
    chronicConditions: [{ type: String }],
    emergencyContact: {
      name: String,
      phone: String,
      relation: String,
    },
    insurance: {
      provider: String,
      policyNumber: String,
    },
  },
  { timestamps: true }
);

export const PatientProfile = model<IPatientProfile>('PatientProfile', patientProfileSchema);

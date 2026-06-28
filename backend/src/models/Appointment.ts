import { Schema, model } from 'mongoose';
import { IAppointment } from '../types';

const appointmentSchema = new Schema<IAppointment>(
  {
    patient: { type: Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    doctor: { type: Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    scheduledAt: { type: Date, required: true },
    duration: { type: Number, default: 30 },
    status: {
      type: String,
      enum: ['pending', 'confirmed', 'cancelled', 'completed'],
      default: 'pending',
    },
    type: { type: String, enum: ['in-person', 'telemedicine'], default: 'in-person' },
    reason: { type: String, required: true },
    notes: String,
    meetingLink: String,
  },
  { timestamps: true }
);

appointmentSchema.index({ scheduledAt: 1, status: 1 });
appointmentSchema.index({ patient: 1, scheduledAt: -1 });

export const Appointment = model<IAppointment>('Appointment', appointmentSchema);

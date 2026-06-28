import { Schema, model } from 'mongoose';
import { IMedicalRecord } from '../types';

const medicalRecordSchema = new Schema<IMedicalRecord>(
  {
    patient: { type: Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    doctor: { type: Schema.Types.ObjectId, ref: 'User' },
    type: {
      type: String,
      enum: ['prescription', 'lab_result', 'imaging', 'discharge_summary', 'consultation'],
      required: true,
    },
    title: { type: String, required: true, trim: true },
    description: { type: String, required: true },
    date: { type: Date, default: Date.now },
    fileUrl: String,
    filePublicId: String,
    tags: [{ type: String, index: true }],
    aiSummary: String,
    isProcessed: { type: Boolean, default: false },
  },
  { timestamps: true }
);

medicalRecordSchema.index({ patient: 1, date: -1 });
medicalRecordSchema.index({ type: 1, patient: 1 });
medicalRecordSchema.index({ tags: 1 });
medicalRecordSchema.index({ title: 'text', description: 'text' });

export const MedicalRecord = model<IMedicalRecord>('MedicalRecord', medicalRecordSchema);

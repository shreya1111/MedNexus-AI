import 'dotenv/config';
import mongoose from 'mongoose';
import { User } from './models/User';
import { PatientProfile } from './models/PatientProfile';
import { MedicalRecord } from './models/MedicalRecord';
import { Appointment } from './models/Appointment';
import { logger } from './utils/logger';

const seed = async () => {
  const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/mednexus';
  await mongoose.connect(uri);
  logger.info('Connected to MongoDB — seeding…');

  // Clean collections
  await Promise.all([
    User.deleteMany({}),
    PatientProfile.deleteMany({}),
    MedicalRecord.deleteMany({}),
    Appointment.deleteMany({}),
  ]);

  // Create demo users
  const [admin, doctor, patient] = await User.create([
    { email: 'admin@mednexus.ai', password: 'Admin@1234', firstName: 'Admin', lastName: 'User', role: 'admin', isEmailVerified: true },
    { email: 'doctor@mednexus.ai', password: 'Doctor@1234', firstName: 'Dr. Arjun', lastName: 'Mehta', role: 'doctor', isEmailVerified: true },
    { email: 'patient@mednexus.ai', password: 'Patient@1234', firstName: 'Priya', lastName: 'Sharma', role: 'patient', isEmailVerified: true },
  ]);

  // Patient profile
  await PatientProfile.create({
    user: patient._id,
    dateOfBirth: new Date('1990-05-15'),
    gender: 'female',
    bloodType: 'B+',
    height: 162,
    weight: 58,
    allergies: ['Penicillin', 'Sulfa drugs'],
    chronicConditions: ['Type 2 Diabetes', 'Mild Hypertension'],
    emergencyContact: { name: 'Rahul Sharma', phone: '+91-9876543210', relation: 'Spouse' },
  });

  // Medical records
  const records = await MedicalRecord.create([
    {
      patient: patient._id,
      doctor: doctor._id,
      type: 'lab_result',
      title: 'HbA1c Blood Test — Q4 2024',
      description: 'Glycated hemoglobin test result: HbA1c 7.2% (target <7%). Fasting glucose: 138 mg/dL. eGFR: 92 mL/min.',
      date: new Date('2024-12-10'),
      tags: ['diabetes', 'hba1c', 'blood-test'],
      aiSummary: 'HbA1c slightly above target. Recommend dietary review and possible medication adjustment.',
      isProcessed: true,
    },
    {
      patient: patient._id,
      doctor: doctor._id,
      type: 'prescription',
      title: 'Metformin 500mg — December 2024',
      description: 'Metformin 500mg twice daily with meals. Continue for 3 months. Monitor for GI side effects.',
      date: new Date('2024-12-10'),
      tags: ['diabetes', 'metformin', 'prescription'],
      isProcessed: false,
    },
    {
      patient: patient._id,
      type: 'imaging',
      title: 'Chest X-Ray — Annual Check',
      description: 'PA view chest radiograph. Lungs clear bilaterally. No infiltrates or effusions. Heart size normal.',
      date: new Date('2024-11-20'),
      tags: ['xray', 'chest', 'annual'],
      isProcessed: true,
    },
    {
      patient: patient._id,
      doctor: doctor._id,
      type: 'consultation',
      title: 'Endocrinology Follow-up',
      description: 'Patient presenting for diabetes management review. BP: 128/82 mmHg. Weight stable. Tolerating Metformin well. Continue current regimen.',
      date: new Date('2024-12-01'),
      tags: ['diabetes', 'endocrinology', 'follow-up'],
      isProcessed: true,
    },
  ]);

  // Appointments
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(10, 0, 0, 0);

  const nextWeek = new Date();
  nextWeek.setDate(nextWeek.getDate() + 7);
  nextWeek.setHours(14, 30, 0, 0);

  await Appointment.create([
    {
      patient: patient._id,
      doctor: doctor._id,
      scheduledAt: tomorrow,
      duration: 30,
      status: 'confirmed',
      type: 'in-person',
      reason: 'Quarterly diabetes review and HbA1c follow-up',
      notes: 'Bring previous lab reports',
    },
    {
      patient: patient._id,
      doctor: doctor._id,
      scheduledAt: nextWeek,
      duration: 45,
      status: 'pending',
      type: 'telemedicine',
      reason: 'Medication side effects consultation',
    },
    {
      patient: patient._id,
      doctor: doctor._id,
      scheduledAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      duration: 30,
      status: 'completed',
      type: 'in-person',
      reason: 'Initial diabetes diagnosis and management plan',
    },
  ]);

  logger.info(`✓ Seeded ${await User.countDocuments()} users`);
  logger.info(`✓ Seeded ${await MedicalRecord.countDocuments()} records`);
  logger.info(`✓ Seeded ${await Appointment.countDocuments()} appointments`);
  logger.info('\n📧 Demo accounts:');
  logger.info('   Admin:   admin@mednexus.ai / Admin@1234');
  logger.info('   Doctor:  doctor@mednexus.ai / Doctor@1234');
  logger.info('   Patient: patient@mednexus.ai / Patient@1234');

  await mongoose.disconnect();
};

seed().catch((err) => { logger.error('Seed failed:', err); process.exit(1); });

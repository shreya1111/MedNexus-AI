import { Response, NextFunction } from 'express';
import { AuthenticatedRequest } from '../types';
import { User } from '../models/User';
import { MedicalRecord } from '../models/MedicalRecord';
import { Appointment } from '../models/Appointment';
import { cacheGet, cacheSet } from '../config/redis';

export const getDashboardStats = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const cacheKey = `analytics:dashboard:${req.user?.role}`;
    const cached = await cacheGet(cacheKey);
    if (cached) return res.json({ success: true, message: 'Analytics', data: JSON.parse(cached) });

    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const [totalPatients, totalRecords, totalAppointments, recentAppointments,
      recordsByType, appointmentsByStatus, newUsersLast30Days] = await Promise.all([
      User.countDocuments({ role: 'patient', isActive: true }),
      MedicalRecord.countDocuments(),
      Appointment.countDocuments(),
      Appointment.find({ scheduledAt: { $gte: now } }).sort('scheduledAt').limit(5)
        .populate('patient doctor', 'firstName lastName'),
      MedicalRecord.aggregate([{ $group: { _id: '$type', count: { $sum: 1 } } }]),
      Appointment.aggregate([{ $group: { _id: '$status', count: { $sum: 1 } } }]),
      User.countDocuments({ role: 'patient', createdAt: { $gte: thirtyDaysAgo } }),
    ]);

    const monthlyRecords = await MedicalRecord.aggregate([
      { $match: { createdAt: { $gte: new Date(now.getFullYear(), now.getMonth() - 5, 1) } } },
      { $group: { _id: { year: { $year: '$createdAt' }, month: { $month: '$createdAt' } }, count: { $sum: 1 } } },
      { $sort: { '_id.year': 1, '_id.month': 1 } },
    ]);

    const stats = {
      overview: { totalPatients, totalRecords, totalAppointments, newUsersLast30Days },
      charts: { recordsByType, appointmentsByStatus, monthlyRecords },
      upcoming: recentAppointments,
    };

    await cacheSet(cacheKey, JSON.stringify(stats), 60);
    res.json({ success: true, message: 'Analytics retrieved', data: stats });
  } catch (err) { next(err); }
};

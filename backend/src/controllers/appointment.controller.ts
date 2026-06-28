import { Response, NextFunction } from 'express';
import { AuthenticatedRequest } from '../types';
import { Appointment } from '../models/Appointment';
import { AppError } from '../middleware/errorHandler';
import { parsePagination, buildPaginationMeta } from '../utils/pagination';

export const createAppointment = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const patientId = req.user?.role === 'patient' ? req.user._id : req.body.patientId;
    const conflict = await Appointment.findOne({
      doctor: req.body.doctorId,
      scheduledAt: { $gte: new Date(req.body.scheduledAt), $lt: new Date(new Date(req.body.scheduledAt).getTime() + 30 * 60000) },
      status: { $in: ['pending', 'confirmed'] },
    });
    if (conflict) return next(new AppError('Doctor is not available at this time', 409));
    const appointment = await Appointment.create({ ...req.body, patient: patientId, doctor: req.body.doctorId });
    res.status(201).json({ success: true, message: 'Appointment booked', data: { appointment } });
  } catch (err) { next(err); }
};

export const getMyAppointments = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { page, limit, skip, sort } = parsePagination(req.query);
    const filter: any = req.user?.role === 'patient' ? { patient: req.user._id } : { doctor: req.user?._id };
    if (req.query.status) filter.status = req.query.status;
    const [appointments, total] = await Promise.all([
      Appointment.find(filter).sort(sort).skip(skip).limit(limit)
        .populate('patient doctor', 'firstName lastName email avatar'),
      Appointment.countDocuments(filter),
    ]);
    res.json({ success: true, message: 'Appointments retrieved', data: { appointments }, pagination: buildPaginationMeta(total, page, limit) });
  } catch (err) { next(err); }
};

export const updateAppointmentStatus = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { status } = req.body;
    const appointment = await Appointment.findByIdAndUpdate(req.params.id, { status }, { new: true });
    if (!appointment) return next(new AppError('Appointment not found', 404));
    res.json({ success: true, message: 'Status updated', data: { appointment } });
  } catch (err) { next(err); }
};

export const cancelAppointment = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const appointment = await Appointment.findById(req.params.id);
    if (!appointment) return next(new AppError('Appointment not found', 404));
    const isPatient = appointment.patient.toString() === req.user?._id.toString();
    const isDoctor = appointment.doctor.toString() === req.user?._id.toString();
    if (!isPatient && !isDoctor && req.user?.role !== 'admin') return next(new AppError('Access denied', 403));
    appointment.status = 'cancelled';
    await appointment.save();
    res.json({ success: true, message: 'Appointment cancelled', data: { appointment } });
  } catch (err) { next(err); }
};

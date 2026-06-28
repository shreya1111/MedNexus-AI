import { Response, NextFunction } from 'express';
import { AuthenticatedRequest } from '../types';
import { PatientProfile } from '../models/PatientProfile';
import { User } from '../models/User';
import { AppError } from '../middleware/errorHandler';
import { parsePagination, buildPaginationMeta } from '../utils/pagination';

export const getMyProfile = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const profile = await PatientProfile.findOne({ user: req.user?._id }).populate('user', '-password');
    if (!profile) return next(new AppError('Profile not found', 404));
    res.json({ success: true, message: 'Profile retrieved', data: { profile } });
  } catch (err) { next(err); }
};

export const updateMyProfile = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const profile = await PatientProfile.findOneAndUpdate(
      { user: req.user?._id },
      { $set: req.body },
      { new: true, runValidators: true, upsert: true }
    );
    res.json({ success: true, message: 'Profile updated', data: { profile } });
  } catch (err) { next(err); }
};

export const getAllPatients = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { page, limit, skip, sort } = parsePagination(req.query);
    const search = req.query.search as string;
    const query: any = { role: 'patient', isActive: true };
    if (search) {
      query.$or = [
        { firstName: new RegExp(search, 'i') },
        { lastName: new RegExp(search, 'i') },
        { email: new RegExp(search, 'i') },
      ];
    }
    const [users, total] = await Promise.all([
      User.find(query).sort(sort).skip(skip).limit(limit),
      User.countDocuments(query),
    ]);
    res.json({
      success: true,
      message: 'Patients retrieved',
      data: { patients: users },
      pagination: buildPaginationMeta(total, page, limit),
    });
  } catch (err) { next(err); }
};

export const getPatientById = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const patient = await User.findOne({ _id: req.params.id, role: 'patient' });
    if (!patient) return next(new AppError('Patient not found', 404));
    const profile = await PatientProfile.findOne({ user: patient._id });
    res.json({ success: true, message: 'Patient retrieved', data: { patient, profile } });
  } catch (err) { next(err); }
};

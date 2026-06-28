import { Response, NextFunction } from 'express';
import { AuthenticatedRequest } from '../types';
import { MedicalRecord } from '../models/MedicalRecord';
import { AppError } from '../middleware/errorHandler';
import { parsePagination, buildPaginationMeta } from '../utils/pagination';
import { uploadToCloudinary, deleteFromCloudinary } from '../services/cloudinary.service';
import { v4 as uuidv4 } from 'uuid';

export const createRecord = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    let fileUrl: string | undefined;
    let filePublicId: string | undefined;

    if (req.file) {
      const { url, publicId } = await uploadToCloudinary(
        req.file.buffer,
        'records',
        `${req.user?._id}-${uuidv4()}`
      );
      fileUrl = url;
      filePublicId = publicId;
    }

    const patientId = req.user?.role === 'patient' ? req.user._id : req.body.patientId;
    const record = await MedicalRecord.create({
      ...req.body,
      patient: patientId,
      doctor: req.user?.role === 'doctor' ? req.user._id : undefined,
      fileUrl,
      filePublicId,
    });

    res.status(201).json({ success: true, message: 'Record created', data: { record } });
  } catch (err) { next(err); }
};

export const getMyRecords = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { page, limit, skip, sort } = parsePagination(req.query);
    const filter: any = { patient: req.user?._id };
    if (req.query.type) filter.type = req.query.type;
    if (req.query.tag) filter.tags = req.query.tag;

    const [records, total] = await Promise.all([
      MedicalRecord.find(filter).sort(sort).skip(skip).limit(limit).populate('doctor', 'firstName lastName'),
      MedicalRecord.countDocuments(filter),
    ]);

    res.json({
      success: true,
      message: 'Records retrieved',
      data: { records },
      pagination: buildPaginationMeta(total, page, limit),
    });
  } catch (err) { next(err); }
};

export const getRecordById = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const record = await MedicalRecord.findById(req.params.id).populate('patient doctor', 'firstName lastName email');
    if (!record) return next(new AppError('Record not found', 404));
    const isOwner = record.patient.toString() === req.user?._id.toString();
    const isDoctor = req.user?.role === 'doctor';
    const isAdmin = req.user?.role === 'admin';
    if (!isOwner && !isDoctor && !isAdmin) return next(new AppError('Access denied', 403));
    res.json({ success: true, message: 'Record retrieved', data: { record } });
  } catch (err) { next(err); }
};

export const updateRecord = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const record = await MedicalRecord.findById(req.params.id);
    if (!record) return next(new AppError('Record not found', 404));
    const isOwner = record.patient.toString() === req.user?._id.toString();
    if (!isOwner && req.user?.role === 'patient') return next(new AppError('Access denied', 403));
    const updated = await MedicalRecord.findByIdAndUpdate(req.params.id, req.body, { new: true });
    res.json({ success: true, message: 'Record updated', data: { record: updated } });
  } catch (err) { next(err); }
};

export const deleteRecord = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const record = await MedicalRecord.findById(req.params.id);
    if (!record) return next(new AppError('Record not found', 404));
    if (record.filePublicId) await deleteFromCloudinary(record.filePublicId);
    await record.deleteOne();
    res.json({ success: true, message: 'Record deleted' });
  } catch (err) { next(err); }
};

export const searchRecords = async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { q, page, limit, skip, sort } = { ...parsePagination(req.query), q: req.query.q as string };
    if (!q) return next(new AppError('Search query required', 400));
    const filter: any = {
      patient: req.user?.role === 'patient' ? req.user._id : undefined,
      $text: { $search: q },
    };
    if (!filter.patient) delete filter.patient;
    const [records, total] = await Promise.all([
      MedicalRecord.find(filter, { score: { $meta: 'textScore' } })
        .sort({ score: { $meta: 'textScore' }, ...sort })
        .skip(skip)
        .limit(limit),
      MedicalRecord.countDocuments(filter),
    ]);
    res.json({
      success: true,
      message: 'Search results',
      data: { records },
      pagination: buildPaginationMeta(total, page, limit),
    });
  } catch (err) { next(err); }
};

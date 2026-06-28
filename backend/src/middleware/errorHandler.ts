import { Request, Response, NextFunction } from 'express';
import { ZodError } from 'zod';
import { logger } from '../utils/logger';

export class AppError extends Error {
  statusCode: number;
  isOperational: boolean;
  constructor(message: string, statusCode: number) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

export const errorHandler = (err: Error, _req: Request, res: Response, _next: NextFunction): void => {
  if (err instanceof AppError) {
    res.status(err.statusCode).json({ success: false, message: err.message });
    return;
  }
  if (err instanceof ZodError) {
    res.status(400).json({
      success: false,
      message: 'Validation error',
      errors: err.issues.map((e) => ({ field: e.path.join('.'), message: e.message })),
    });
    return;
  }
  const mongoErr = err as any;
  if (mongoErr.name === 'MongoServerError' && mongoErr.code === 11000) {
    const field = Object.keys(mongoErr.keyValue || {})[0] || 'field';
    res.status(409).json({ success: false, message: `${field} already exists` });
    return;
  }
  if (err.name === 'CastError') {
    res.status(400).json({ success: false, message: 'Invalid ID format' });
    return;
  }
  logger.error('Unhandled error:', err);
  res.status(500).json({ success: false, message: 'Internal server error' });
};

export const notFound = (_req: Request, res: Response): void => {
  res.status(404).json({ success: false, message: 'Route not found' });
};

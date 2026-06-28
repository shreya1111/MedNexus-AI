import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../utils/logger';

declare global {
  namespace Express {
    interface Request {
      id?: string;
    }
  }
}

export const requestId = (req: Request, res: Response, next: NextFunction): void => {
  const id = req.headers['x-request-id'] as string || uuidv4();
  req.id = id;
  res.setHeader('X-Request-ID', id);
  
  // Log request with ID
  logger.info(`[${id}] ${req.method} ${req.path}`, {
    requestId: id,
    method: req.method,
    path: req.path,
    ip: req.ip,
  });
  
  next();
};

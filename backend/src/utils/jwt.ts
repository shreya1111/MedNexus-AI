import jwt, { SignOptions } from 'jsonwebtoken';
import { Types } from 'mongoose';
import { UserRole } from '../types';

interface TokenPayload {
  userId: string;
  role: UserRole;
}

export const generateAccessToken = (userId: Types.ObjectId, role: UserRole): string => {
  const opts: SignOptions = { expiresIn: (process.env.JWT_EXPIRES_IN || '15m') as SignOptions['expiresIn'] };
  return jwt.sign({ userId: userId.toString(), role }, process.env.JWT_SECRET || 'fallback-secret', opts);
};

export const generateRefreshToken = (userId: Types.ObjectId, role: UserRole): string => {
  const opts: SignOptions = { expiresIn: (process.env.JWT_REFRESH_EXPIRES_IN || '7d') as SignOptions['expiresIn'] };
  return jwt.sign({ userId: userId.toString(), role }, process.env.JWT_REFRESH_SECRET || 'fallback-refresh-secret', opts);
};

export const verifyAccessToken = (token: string): TokenPayload =>
  jwt.verify(token, process.env.JWT_SECRET || 'fallback-secret') as TokenPayload;

export const verifyRefreshToken = (token: string): TokenPayload =>
  jwt.verify(token, process.env.JWT_REFRESH_SECRET || 'fallback-refresh-secret') as TokenPayload;

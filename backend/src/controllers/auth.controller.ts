import { Response, NextFunction } from 'express';
import { AuthenticatedRequest, ApiResponse } from '../types';
import { User } from '../models/User';
import { PatientProfile } from '../models/PatientProfile';
import { generateAccessToken, generateRefreshToken, verifyRefreshToken } from '../utils/jwt';
import { AppError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

export const register = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { email, password, firstName, lastName, role } = req.body;
    const exists = await User.findOne({ email });
    if (exists) return next(new AppError('Email already registered', 409));

    const user = await User.create({ email, password, firstName, lastName, role });
    if (role === 'patient') {
      await PatientProfile.create({ user: user._id });
    }

    const accessToken = generateAccessToken(user._id, user.role);
    const refreshToken = generateRefreshToken(user._id, user.role);
    await User.findByIdAndUpdate(user._id, { $push: { refreshTokens: refreshToken } });

    res.status(201).json({
      success: true,
      message: 'Account created successfully',
      data: { user, accessToken, refreshToken },
    } as ApiResponse);
  } catch (err) {
    next(err);
  }
};

export const login = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email, isActive: true }).select('+password +refreshTokens');
    if (!user || !(await user.comparePassword(password))) {
      return next(new AppError('Invalid credentials', 401));
    }

    const accessToken = generateAccessToken(user._id, user.role);
    const refreshToken = generateRefreshToken(user._id, user.role);
    
    user.refreshTokens = (user.refreshTokens || []).slice(-4);
    user.refreshTokens.push(refreshToken);
    user.lastLogin = new Date();
    await user.save();

    const safeUser = user.toJSON();
    res.json({
      success: true,
      message: 'Login successful',
      data: { user: safeUser, accessToken, refreshToken },
    } as ApiResponse);
  } catch (err) {
    next(err);
  }
};

export const refreshToken = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { refreshToken: token } = req.body;
    const decoded = verifyRefreshToken(token);
    const user = await User.findById(decoded.userId).select('+refreshTokens');
    if (!user || !user.refreshTokens?.includes(token)) {
      return next(new AppError('Invalid refresh token', 401));
    }

    const newAccessToken = generateAccessToken(user._id, user.role);
    const newRefreshToken = generateRefreshToken(user._id, user.role);
    user.refreshTokens = user.refreshTokens.filter((t) => t !== token);
    user.refreshTokens.push(newRefreshToken);
    await user.save();

    res.json({
      success: true,
      message: 'Token refreshed',
      data: { accessToken: newAccessToken, refreshToken: newRefreshToken },
    });
  } catch {
    next(new AppError('Invalid refresh token', 401));
  }
};

export const logout = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { refreshToken: token } = req.body;
    if (req.user && token) {
      await User.findByIdAndUpdate(req.user._id, { $pull: { refreshTokens: token } });
    }
    res.json({ success: true, message: 'Logged out successfully' });
  } catch (err) {
    next(err);
  }
};

export const getMe = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const user = await User.findById(req.user?._id);
    if (!user) return next(new AppError('User not found', 404));
    res.json({ success: true, message: 'Profile retrieved', data: { user } });
  } catch (err) {
    next(err);
  }
};

export const updateProfile = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { firstName, lastName, avatar } = req.body;
    const user = await User.findByIdAndUpdate(
      req.user?._id,
      { $set: { firstName, lastName, avatar } },
      { new: true, runValidators: true }
    );
    if (!user) return next(new AppError('User not found', 404));
    res.json({ success: true, message: 'Profile updated', data: { user } });
  } catch (err) {
    next(err);
  }
};

export const changePassword = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { currentPassword, newPassword } = req.body;
    const user = await User.findById(req.user?._id).select('+password');
    if (!user || !(await user.comparePassword(currentPassword))) {
      return next(new AppError('Current password is incorrect', 400));
    }
    user.password = newPassword;
    await user.save();
    res.json({ success: true, message: 'Password changed successfully' });
  } catch (err) {
    next(err);
  }
};

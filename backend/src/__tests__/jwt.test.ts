import { generateAccessToken, generateRefreshToken, verifyAccessToken, verifyRefreshToken } from '../utils/jwt';
import { Types } from 'mongoose';

process.env.JWT_SECRET = 'test-jwt-secret-minimum-32-chars-long!!';
process.env.JWT_REFRESH_SECRET = 'test-refresh-secret-minimum-32-chars!!';
process.env.JWT_EXPIRES_IN = '15m';
process.env.JWT_REFRESH_EXPIRES_IN = '7d';

describe('JWT Utilities', () => {
  const userId = new Types.ObjectId();
  const role = 'patient' as const;

  it('generates a valid access token', () => {
    const token = generateAccessToken(userId, role);
    expect(typeof token).toBe('string');
    expect(token.split('.')).toHaveLength(3);
  });

  it('generates a valid refresh token', () => {
    const token = generateRefreshToken(userId, role);
    expect(typeof token).toBe('string');
    expect(token.split('.')).toHaveLength(3);
  });

  it('verifies access token and returns payload', () => {
    const token = generateAccessToken(userId, role);
    const payload = verifyAccessToken(token);
    expect(payload.userId).toBe(userId.toString());
    expect(payload.role).toBe(role);
  });

  it('verifies refresh token and returns payload', () => {
    const token = generateRefreshToken(userId, role);
    const payload = verifyRefreshToken(token);
    expect(payload.userId).toBe(userId.toString());
    expect(payload.role).toBe(role);
  });

  it('throws on invalid access token', () => {
    expect(() => verifyAccessToken('invalid.token.here')).toThrow();
  });

  it('throws on invalid refresh token', () => {
    expect(() => verifyRefreshToken('bad.refresh.token')).toThrow();
  });

  it('generates different tokens for different users', () => {
    const user2 = new Types.ObjectId();
    const t1 = generateAccessToken(userId, role);
    const t2 = generateAccessToken(user2, role);
    expect(t1).not.toBe(t2);
  });
});

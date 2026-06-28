import IORedis from 'ioredis';
import { logger } from '../utils/logger';

let redisClient: IORedis | null = null;

export const getRedisClient = (): IORedis | null => {
  if (!redisClient) {
    try {
      redisClient = new IORedis(process.env.REDIS_URL || 'redis://localhost:6379', {
        enableOfflineQueue: false,
        lazyConnect: true,
        retryStrategy: (times: number) => {
          if (times > 3) return null;
          return Math.min(times * 50, 2000);
        },
      });
      redisClient.on('error', (err) => logger.warn('Redis error (non-fatal):', err.message));
      redisClient.on('connect', () => logger.info('Redis connected'));
    } catch (err) {
      logger.warn('Redis unavailable, continuing without cache');
    }
  }
  return redisClient;
};

export const cacheGet = async (key: string): Promise<string | null> => {
  const client = getRedisClient();
  if (!client) return null;
  try {
    return await client.get(key);
  } catch {
    return null;
  }
};

export const cacheSet = async (key: string, value: string, ttl = 300): Promise<void> => {
  const client = getRedisClient();
  if (!client) return;
  try {
    await client.setex(key, ttl, value);
  } catch {}
};

export const cacheDel = async (key: string): Promise<void> => {
  const client = getRedisClient();
  if (!client) return;
  try {
    await client.del(key);
  } catch {}
};

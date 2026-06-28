import { z } from 'zod';
import { logger } from '../utils/logger';

const envSchema = z.object({
  // Server
  PORT: z.string().default('5000'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  FRONTEND_URL: z.string().url().default('http://localhost:3000'),

  // Database
  MONGODB_URI: z.string().min(1, 'MONGODB_URI is required'),

  // JWT
  JWT_SECRET: z.string().min(32, 'JWT_SECRET must be at least 32 characters'),
  JWT_REFRESH_SECRET: z.string().min(32, 'JWT_REFRESH_SECRET must be at least 32 characters'),
  JWT_EXPIRES_IN: z.string().default('15m'),
  JWT_REFRESH_EXPIRES_IN: z.string().default('7d'),

  // Redis (optional)
  REDIS_URL: z.string().optional(),

  // Cloudinary (optional but required for file uploads)
  CLOUDINARY_CLOUD_NAME: z.string().optional(),
  CLOUDINARY_API_KEY: z.string().optional(),
  CLOUDINARY_API_SECRET: z.string().optional(),

  // External services
  AI_SERVICE_URL: z.string().url().default('http://localhost:8000'),
});

export type Env = z.infer<typeof envSchema>;

export function validateEnv(): Env {
  try {
    const env = envSchema.parse(process.env);
    logger.info('Environment variables validated successfully');
    
    // Warnings for optional but recommended variables
    if (!env.REDIS_URL) {
      logger.warn('REDIS_URL not set - caching will be disabled');
    }
    if (!env.CLOUDINARY_CLOUD_NAME || !env.CLOUDINARY_API_KEY || !env.CLOUDINARY_API_SECRET) {
      logger.warn('Cloudinary credentials not set - file uploads will fail');
    }
    
    return env;
  } catch (error) {
    if (error instanceof z.ZodError) {
      logger.error('Environment variable validation failed:');
      error.issues.forEach((issue) => {
        logger.error(`  - ${issue.path.join('.')}: ${issue.message}`);
      });
      logger.error('\nPlease check your .env file and ensure all required variables are set.');
      logger.error('See backend/.env.example for reference.\n');
    }
    process.exit(1);
  }
}

export const env = validateEnv();

import 'dotenv/config';
import { validateEnv } from './config/env';
import { httpServer } from './app';
import { connectDB } from './config/database';
import { getRedisClient } from './config/redis';
import { logger } from './utils/logger';

// Validate environment variables first
validateEnv();

const PORT = parseInt(process.env.PORT || '5000', 10);

const start = async () => {
  await connectDB();
  getRedisClient();

  httpServer.listen(PORT, '0.0.0.0', () => {
    logger.info(`MedNexus AI Backend running on port ${PORT}`);
    logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
  });
};

process.on('unhandledRejection', (reason) => {
  logger.error('Unhandled Rejection:', reason);
  process.exit(1);
});

process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');
  httpServer.close(() => process.exit(0));
});

start();

import 'express-async-errors';
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import morgan from 'morgan';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { createServer } from 'http';
import { Server as SocketServer } from 'socket.io';
import path from 'path';
import fs from 'fs';

import { requestId } from './middleware/requestId';
import authRoutes from './routes/auth.routes';
import patientRoutes from './routes/patient.routes';
import recordRoutes from './routes/medicalRecord.routes';
import appointmentRoutes from './routes/appointment.routes';
import analyticsRoutes from './routes/analytics.routes';
import { errorHandler, notFound } from './middleware/errorHandler';
import { logger } from './utils/logger';

// Ensure logs dir
const logsDir = path.join(process.cwd(), 'logs');
if (!fs.existsSync(logsDir)) fs.mkdirSync(logsDir, { recursive: true });

const app = express();
const httpServer = createServer(app);

export const io = new SocketServer(httpServer, {
  cors: { origin: process.env.FRONTEND_URL || 'http://localhost:3000', methods: ['GET', 'POST'] },
});

// Security
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

// Rate limiting
app.use('/api/v1/auth', rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  message: { success: false, message: 'Too many requests, please try again later' },
}));

app.use(rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 200,
}));

// Middleware
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(requestId);
app.use(morgan('combined', { stream: { write: (msg) => logger.info(msg.trim()) } }));

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString(), version: '1.0.0' });
});

// API Routes
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/patients', patientRoutes);
app.use('/api/v1/records', recordRoutes);
app.use('/api/v1/appointments', appointmentRoutes);
app.use('/api/v1/analytics', analyticsRoutes);

// WebSocket
io.on('connection', (socket) => {
  logger.info(`Socket connected: ${socket.id}`);
  socket.on('join:room', (roomId: string) => socket.join(roomId));
  socket.on('leave:room', (roomId: string) => socket.leave(roomId));
  socket.on('disconnect', () => logger.info(`Socket disconnected: ${socket.id}`));
});

// Error handling
app.use(notFound);
app.use(errorHandler);

export { app, httpServer };

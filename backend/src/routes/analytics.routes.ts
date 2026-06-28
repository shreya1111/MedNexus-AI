import { Router } from 'express';
import { getDashboardStats } from '../controllers/analytics.controller';
import { authenticate, authorize } from '../middleware/auth';

const router = Router();

router.get('/dashboard', authenticate, authorize('doctor', 'admin'), getDashboardStats);

export default router;

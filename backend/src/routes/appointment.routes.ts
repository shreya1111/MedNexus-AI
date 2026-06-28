import { Router } from 'express';
import { createAppointment, getMyAppointments, updateAppointmentStatus, cancelAppointment } from '../controllers/appointment.controller';
import { authenticate } from '../middleware/auth';

const router = Router();

router.use(authenticate);
router.get('/', getMyAppointments);
router.post('/', createAppointment);
router.put('/:id/status', updateAppointmentStatus);
router.put('/:id/cancel', cancelAppointment);

export default router;

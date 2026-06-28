import { Router } from 'express';
import { getMyProfile, updateMyProfile, getAllPatients, getPatientById } from '../controllers/patient.controller';
import { authenticate, authorize } from '../middleware/auth';

const router = Router();

router.use(authenticate);
router.get('/profile', authorize('patient'), getMyProfile);
router.put('/profile', authorize('patient'), updateMyProfile);
router.get('/', authorize('doctor', 'admin'), getAllPatients);
router.get('/:id', authorize('doctor', 'admin'), getPatientById);

export default router;

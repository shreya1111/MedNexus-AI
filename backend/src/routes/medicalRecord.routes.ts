import { Router } from 'express';
import { createRecord, getMyRecords, getRecordById, updateRecord, deleteRecord, searchRecords } from '../controllers/medicalRecord.controller';
import { authenticate } from '../middleware/auth';
import { upload } from '../middleware/upload';

const router = Router();

router.use(authenticate);
router.get('/', getMyRecords);
router.get('/search', searchRecords);
router.get('/:id', getRecordById);
router.post('/', upload.single('file'), createRecord);
router.put('/:id', updateRecord);
router.delete('/:id', deleteRecord);

export default router;

import express from 'express';
import { generateBrollPlan } from '../controllers/brollController.js';
import { brollUpload } from '../middlewares/uploadMiddleware.js';

const router = express.Router();

// Route: Handle video processing
router.post('/process', brollUpload, generateBrollPlan);

export default router;
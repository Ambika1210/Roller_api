import { processVideo } from '../services/brollService.js';
import path from 'path';
import logger from '../utils/logger.js';
import { setSuccess, setServerError, setBadRequest } from '../utils/responseHelper.js';

export const generateBrollPlan = async (req, res) => {
  const startTime = Date.now();
  
  try {
    if (!req.files || !req.files['a_roll']) {
      logger.warn('[B-Roll Controller] Request missing a_roll file');
      return setBadRequest(res, 'A-roll video is required');
    }

    const aRollFile = req.files['a_roll'][0];
    const bRollFiles = req.files['b_rolls'] || [];

    const aRollPath = path.resolve(aRollFile.path);
    const bRollPaths = bRollFiles.map(f => path.resolve(f.path));

    logger.info(`[B-Roll Controller] Starting job. A-Roll: ${aRollFile.originalname}, B-Rolls: ${bRollFiles.length}`);

    const plan = await processVideo(aRollPath, bRollPaths);

    const duration = Date.now() - startTime;
    logger.info(`[B-Roll Controller] Job completed in ${duration}ms`);

    setSuccess(res, {
        message: 'B-roll plan generated successfully',
        plan: plan,
        meta: {
            processing_time_ms: duration,
            clip_count: bRollFiles.length
        }
    });

  } catch (error) {
    logger.error(`[B-Roll Controller] Error processing request: ${error.message}`);
    setServerError(res, error.message);
  }
};
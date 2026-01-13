import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';
import logger from '../utils/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const processVideo = async (aRollPath, bRollPaths) => {
  return new Promise((resolve, reject) => {
    
    const pythonScriptPath = path.join(__dirname, '../python/broll_engine.py');
    const pythonExecutable = path.resolve('src/python/venv/Scripts/python.exe');

    const args = [
      pythonScriptPath,
      '--a_roll', aRollPath,
      '--b_rolls', ...bRollPaths
    ];

    logger.info(`[B-Roll Service] Spawning Python Process: ${pythonExecutable}`);

    const pythonProcess = spawn(pythonExecutable, args);

    let stdoutData = '';
    let stderrData = '';

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      stdoutData += output;
      if (!output.includes('JSON_PLAN')) {
         logger.info(`[Python stdout]: ${output.trim()}`);
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      const msg = data.toString();
      stderrData += msg;
      logger.error(`[Python stderr]: ${msg.trim()}`);
    });

    pythonProcess.on('close', async (code) => {
      if (code !== 0) {
        logger.error(`[B-Roll Service] Process exited with code ${code}`);
        return reject(new Error(`Python process error: ${stderrData}`));
      }

      try {
        const plan = extractJsonPlan(stdoutData);
        logger.info(`[B-Roll Service] Successfully generated plan with ${plan.insertions?.length || 0} insertions.`);

        await cleanupFiles();
        resolve(plan);
      } catch (err) {
        logger.error(`[B-Roll Service] JSON Parse Failed: ${err.message}`);
        reject(new Error('Failed to parse Python output'));
      }
    });

    pythonProcess.on('error', (err) => {
      logger.error(`[B-Roll Service] Spawn Error: ${err.message}`);
      reject(new Error(`Failed to start subprocess: ${err.message}`));
    });

    async function cleanupFiles() {
      try {
        await fs.unlink(aRollPath);
        for (const p of bRollPaths) await fs.unlink(p);
        logger.info('[B-Roll Service] Cleaned up uploaded files.');
      } catch (cleanupErr) {
        logger.error(`[B-Roll Service] Cleanup failed: ${cleanupErr.message}`);
      }
    }
  });
};

const extractJsonPlan = (output) => {
  const startMarker = 'JSON_PLAN_START';
  const endMarker = 'JSON_PLAN_END';
  
  const startIndex = output.indexOf(startMarker);
  const endIndex = output.indexOf(endMarker);

  if (startIndex !== -1 && endIndex !== -1) {
    const jsonStr = output.substring(startIndex + startMarker.length, endIndex).trim();
    return JSON.parse(jsonStr);
  }
  
  throw new Error('JSON markers not found in output');
};
import jwt from 'jsonwebtoken';
import NodeCache from 'node-cache';
import mongoose from 'mongoose';
import serverConfig from '../config/config.js';
import User from '../models/user.model.js';
import logger from '../utils/logger.js';

const tokenCache = new NodeCache({ stdTTL: 60 });

function verifyToken(token) {
  const cached = tokenCache.get(token);
  if (cached) return cached;

  const decoded = jwt.verify(token, serverConfig.JWT_SECRET);
  tokenCache.set(token, decoded);
  return decoded;
}

function generateToken(userId) {
  return jwt.sign(userId, serverConfig.JWT_SECRET, {
    expiresIn: serverConfig.JWT_EXPIRES_IN,
  });
}

function checkPermission() {
  return async (req, res, next) => {
    try {
      const authHeader = req.headers.authorization;
      const token = authHeader?.startsWith('Bearer ')
        ? authHeader.split(' ')[1]
        : null;

      if (!token) {
        return res.status(401).json({
          success: false,
          message: 'Token required',
        });
      }

      const payload = verifyToken(token);
      const { userId } = payload;

      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'Invalid token',
        });
      }

      const user = await User.findById(new mongoose.Types.ObjectId(userId)).lean();

      if (!user) {
        return res.status(404).json({
          success: false,
          message: 'User not found',
        });
      }

      if (!user.isActive) {
        return res.status(403).json({
          success: false,
          message: 'User inactive',
        });
      }

      next();
    } catch (err) {
      logger.error(`Auth Error: ${err.message}`);

      return res.status(401).json({
        success: false,
        message: 'Invalid or expired token',
      });
    }
  };
}

export { checkPermission, generateToken };
export default { checkPermission };

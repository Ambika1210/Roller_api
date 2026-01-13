import User from "../models/user.model.js"

import logger from '../utils/logger.js';
import mongoose from 'mongoose';

class UserRepo {
  
  createUser = async (data) => {
    try {
      logger.info(`UserRepo >>>> createUser >>>> Creating user with email: ${data.email}, role: ${data.role}`);
      const user = await User.create(data);
      
      logger.info(`UserRepo >>>> createUser >>>> User created successfully with userId: ${user._id}, email: ${user.email}, role: ${user.role}`);
      return user;
    } catch (error) {
      logger.error(`UserRepo >>>> createUser >>>> Error creating user: ${error.message}`, {
        stack: error.stack,
        email: data?.email
      });
      throw error;
    }
  };

getUserById = async (userId) => {
    try {
      logger.info(`UserRepo >>>> getUserById >>>> Fetching user: ${userId}`);
      const user = await User.findById(userId).lean();
      
      if (user) {
        logger.info(`UserRepo >>>> getUserById >>>> User found with userId: ${userId}`);
      } else {
        logger.info(`UserRepo >>>> getUserById >>>> No user found with userId: ${userId}`);
      }
      
      return user;
    } catch (error) {
      logger.error(`UserRepo >>>> getUserById >>>> Error fetching user: ${error.message}`, {
        stack: error.stack,
        userId
      });
      throw error;
    }
  };

  loginUser = async (email, password) => {
  try {
    logger.info(`UserRepo >>>> loginUser >>>> Attempting login for email: ${email}`);

    const user = await User.findOne({ email })
      .select("+password")
      .lean();

    if (!user) {
      logger.info(`UserRepo >>>> loginUser >>>> No user found with email: ${email}`);
      throw new Error("user not found");
    }

    return user;
  } catch (error) {
    logger.error( `UserRepo >>>> loginUser >>>> Error during login: ${error.message}`, { email,});
    throw error;
  }
};

}

export default new UserRepo()
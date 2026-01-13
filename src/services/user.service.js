import { generateToken } from "../middlewares/auth.middleware.js";
import userRepo from "../repositories/user.repository.js";
import logger from "../utils/logger.js";
import bcrypt from "bcryptjs";

class UserService {
  createUser = async (data) => {
    try {
      logger.info(
        `UserService >>>> createUser >>>> Creating user with email: ${data?.email}`
      );

      if (!data?.name || !data?.email || !data?.password) {
        throw new Error("Name, email and password are required");
      }

      const salt = await bcrypt.genSalt(10);
      data.password = await bcrypt.hash(data.password, salt);

      const user = await userRepo.createUser(data);

      logger.info(
        `UserService >>>> createUser >>>> User created successfully with userId: ${user._id}`
      );

      return user;
    } catch (error) {
      logger.error(
        `UserService >>>> createUser >>>> Error creating user: ${error.message}`,
        {
          stack: error.stack,
          email: data?.email,
        }
      );
      throw error;
    }
  };

  getUserById = async (userId) => {
    try {
      logger.info(
        `UserService >>>> getUserById >>>> Fetching user with userId: ${userId}`
      );

      if (!userId) {
        throw new Error("UserId is required");
      }

      const user = await userRepo.getUserById(userId);

      if (!user) {
        logger.info(
          `UserService >>>> getUserById >>>> No user found with userId: ${userId}`
        );
        return null;
      }

      logger.info(
        `UserService >>>> getUserById >>>> User fetched successfully with userId: ${userId}`
      );

      return user;
    } catch (error) {
      logger.error(
        `UserService >>>> getUserById >>>> Error fetching user: ${error.message}`,
        {
          stack: error.stack,
          userId,
        }
      );
      throw error;
    }
  };

  loginUser = async (email, password) => {
    try {
      logger.info(`UserService >>>> loginUser >>>> Login attempt for email: ${email}`);

      

      const user = await userRepo.loginUser(email);

      if (!user) {
        logger.info(`UserService >>>> loginUser >>>> Invalid login credentials for email: ${email}`);
        throw new Error("user not found");
      }
      if (!user.isActive) {
      logger.info(`UserRepo >>>> loginUser >>>> User is inactive: ${email}`);
      throw new Error("user is inactive");
    }
    const isMatched = await bcrypt.compare(password,user.password)

    if(!isMatched){
      throw new Error("Invalid password")
    }
    const token = await generateToken({userId:user._id})


      logger.info(`UserService >>>> loginUser >>>> Login successful for email: ${email}`);

      return {user,token};
    } catch (error) {
      logger.error(
        `UserService >>>> loginUser >>>> Error during login: ${error.message}`,
        {
          stack: error.stack,
          email,
        }
      );
      throw error;
    }
  };
}

export default new UserService();

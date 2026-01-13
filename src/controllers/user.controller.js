import userService from "../services/user.service.js";
import logger from "../utils/logger.js";
import { setSuccess, setCreateSuccess, setServerError, setBadRequest, setNotFoundError } from '../utils/responseHelper.js';

class UserController {

  createUser = async (req, res) => {
    try {
      logger.info(`UserController >>>> createUser >>>> Request received to create user`);

      const user = await userService.createUser(req.body);
     logger.info(`UserController >>>> createUser >>>> User created successfully with userId: ${user._id}` );
        return setCreateSuccess(res, {
        message: "User created successfully",
        user: user,
    });
    } catch (error) {
      logger.error(`UserController >>>> createUser >>>> Error creating user: ${error.message}`,
        { stack: error.stack });

      return setServerError(res, error.message || "Failed to create user");
    }
  };

  getUserById = async (req, res) => {
    try {
      const { userId } = req.params;

      logger.info(`UserController >>>> getUserById >>>> Fetching user with userId: ${userId}`);

      const user = await userService.getUserById(userId);

      logger.info(`UserController >>>> getUserById >>>> User fetched successfully with userId: ${userId}`);

      return setSuccess(res, user);
    } catch (error) {
      logger.error(`UserController >>>> getUserById >>>> Error fetching user: ${error.message}`,
        {
          stack: error.stack,
          userId: req.params?.userId,
        }
      );

      return setServerError(res, error.message || "Failed to fetch user");
    }
  };

  loginUser = async (req, res) => {
    try {
      const { email, password } = req.body;
      if (!email || !password) {
        return setBadRequest(res, "Email and password are required");
      }
      logger.info( `UserController >>>> loginUser >>>> Login request received for email: ${email}`);

      const user = await userService.loginUser(email, password);

      logger.info(`UserController >>>> loginUser >>>> Login successful for email: ${email}`);

      return setSuccess(res, {
        message: "Login successful",
        user: user,
      });
    } catch (error) {
      logger.error( `UserController >>>> loginUser >>>> Error during login: ${error.message}`,{email: req.body?.email,});
      if(error.message =="user not found" || "user is inactive" ||"Invalid password"){
        return setBadRequest(res, error.message);
      }
      return setServerError(res, error.message);
    }
  };
}

export default new UserController();

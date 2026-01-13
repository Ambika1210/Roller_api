import userService from "../services/user.service.js";
import logger from "../utils/logger.js";

class UserController {

  createUser = async (req, res) => {
    try {
      logger.info(`UserController >>>> createUser >>>> Request received to create user`);

      const user = await userService.createUser(req.body);
     logger.info(`UserController >>>> createUser >>>> User created successfully with userId: ${user._id}` );
        return res.status(201).json({
        success: true,
        message: "User created successfully",
        data: user,
    });
    } catch (error) {
      logger.error(`UserController >>>> createUser >>>> Error creating user: ${error.message}`,
        { stack: error.stack });

      return res.status(500).json({
        success: false,
        message: error.message || "Failed to create user",
      });
    }
  };

  getUserById = async (req, res) => {
    try {
      const { userId } = req.params;

      logger.info(`UserController >>>> getUserById >>>> Fetching user with userId: ${userId}`);

      const user = await userService.getUserById(userId);

      if (!user) {
        return res.status(404).json({
          success: false,
          message: "User not found",
        });
      }

      logger.info(`UserController >>>> getUserById >>>> User fetched successfully with userId: ${userId}`);

      return res.status(200).json({
        success: true,
        data: user,
      });
    } catch (error) {
      logger.error(`UserController >>>> getUserById >>>> Error fetching user: ${error.message}`,
        {
          stack: error.stack,
          userId: req.params?.userId,
        }
      );

      return res.status(500).json({
        success: false,
        message: error.message || "Failed to fetch user",
      });
    }
  };

  loginUser = async (req, res) => {
    try {
      const { email, password } = req.body;
      if (!email || !password) {
        return res.status(401).json({
          success:false,
          message:"Email and password are required"});
      }
      logger.info( `UserController >>>> loginUser >>>> Login request received for email: ${email}`);

      const user = await userService.loginUser(email, password);

      logger.info(`UserController >>>> loginUser >>>> Login successful for email: ${email}`);

      return res.status(200).json({
        success: true,
        message: "Login successful",
        data: user,
      });
    } catch (error) {
      logger.error( `UserController >>>> loginUser >>>> Error during login: ${error.message}`,{email: req.body?.email,});
      if(error.message =="user not found" || "user is inactive" ||"Invalid password"){
        return res.status(400).json({
          success:false,
          message: error.message
        })
      }
      return res.status(500).json({
        success: false,
        message: error.message,
      });
    }
  };
}

export default new UserController();

import express from "express";
import userController from "../controllers/user.controller.js";
// import authMiddleware from "../middlewares/auth.middleware.js";

const router = express.Router();

router.post("/user/register", userController.createUser);
router.post("/user/login", userController.loginUser);
router.get("/:userId/user", userController.getUserById);

export default router;

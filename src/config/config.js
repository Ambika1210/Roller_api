import dotenv from "dotenv";

dotenv.config();

const config = {
  PORT: process.env.PORT || 7173, // Changed port to avoid conflict with institute_api (3001)
  STAGE: process.env.STAGE,
  JWT_SECRET: process.env.JWT_SECRET || "abcdert",
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || "7d",
  MONGO_URL:process.env.MONGO_URL || "mongodb+srv://ambikaambika1210_db_user:ZLLntawVCWuS9ofT@gplbackend.jwcppn6.mongodb.net/roller_assignment?retryWrites=true&w=majority&appName=gplbackend",

 LOG_MAX_FILES: process.env.LOG_MAX_FILES || "14d",
};

export default config;

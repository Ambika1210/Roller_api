import mongoose from 'mongoose';
import logger from '../utils/logger.js';

class MongoWrapper {

  constructor(uri, options = {}) {
    this.uri = uri;

    const defaultOptions = {
      maxPoolSize: 50,
      minPoolSize: 20,
    };

    this.options = {
      ...defaultOptions,
      ...options,
    };
  }

  async connect() {
    try {
      await mongoose.connect(this.uri, this.options);
      logger.info('Connected to MongoDB successfully');
    } catch (error) {
      logger.error(`Error connecting to MongoDB: ${error.message}, stack: ${error.stack}`);
      throw error;
    }
  }

  async disconnect() {
    try {
      await mongoose.disconnect();
      logger.info('Disconnected from MongoDB');
    } catch (error) {
      logger.error(`Error disconnecting from MongoDB: ${error.message}, stack: ${error.stack}`);
      throw error;
    }
  }
}

mongoose.set('debug', true);
export default MongoWrapper;

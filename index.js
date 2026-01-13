import express from 'express';
import { createServer } from 'http';
import dotenv from 'dotenv';
dotenv.config();

import compression from 'compression';
import bodyParser from 'body-parser';
import cookieParser from 'cookie-parser';


import serverConfig from './src/config/config.js';
import chalk from './src/utils/chalk.js';
import DatabaseConnection from './src/config/mongoWrapper.js';
import logger from './src/utils/logger.js';
import brollRoutes from './src/routes/broll.routes.js';
import userRoutes from './src/routes/user.route.js'

let dbConnection;
const app = express();
const server = createServer(app);

// Connect to MongoDB
(async () => {
  try {
    dbConnection = new DatabaseConnection(serverConfig.MONGO_URL);
    await dbConnection.connect();
  } catch (error) {
    logger.error('Error during MongoDB operations:', error);
  }
})();

app.use(compression());
// database connection
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'PUT, GET, POST, DELETE, OPTIONS, PATCH');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Access-Control-Allow-Credentials');
  res.header('Access-Control-Allow-Credentials', 'false');
  res.header('Access-Control-Max-Age', '86400');
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ limit: '100mb', extended: false }));
app.use(cookieParser());

// Request logging
app.use('*', (req, res, next) => {
  const { hostname, originalUrl, protocol, method } = req;
  logger.info(`${method === 'GET' ? chalk.getReq(method) : chalk.postReq(method)}  ${protocol}://${hostname}:${serverConfig.PORT}${originalUrl}`);
  next();
});

// Routes
app.get('/', (req, res) => {
  res.send('Roller API is running');
});

app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'success',
    message: 'Health check passed',
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

// API Routes
app.use('/api/broll', brollRoutes);
app.use('/api',userRoutes)

server.listen(serverConfig.PORT, () => {
  logger.info(`index.js << Server listening on port ${serverConfig.PORT}`);
  console.log(`Server running on http://localhost:${serverConfig.PORT}`);
});

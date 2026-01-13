import winston from 'winston';
import { v4 as uuidv4 } from 'uuid';
import 'winston-daily-rotate-file';
import { format, createLogger, transports } from 'winston';
import { LOG_FILENAME, DATE_PATTERN } from '../constants/log_constants.js';
import { ENV_PRODUCTION, INFO, DEBUG } from '../constants/enums.js';
import config from '../config/config.js';
const { combine, timestamp, printf } = winston.format;

const fileRotateTransport = new transports.DailyRotateFile({
  filename: LOG_FILENAME,
  datePattern: DATE_PATTERN,
  maxFiles: config.LOG_MAX_FILES,
});

const myFormat = printf(({ timestamp, level, message, meta, traceID }) => {
  return `${timestamp}|${level}|traceID: ${traceID}|${message}${meta ? '| ' + JSON.stringify(meta) : ''}`;
});

const generateTraceID = () => {
  return uuidv4();
};

const logger = createLogger({
  level: config.STAGE === ENV_PRODUCTION ? INFO : DEBUG,
  format: combine(
    format.colorize(),
    timestamp({
      format: 'MM-DD-YY HH:mm:ss',
    }),
    format(info => {
      info.traceID = generateTraceID();
      return info;
    })(),
    myFormat
  ),
  transports: [fileRotateTransport, new transports.Console()],
});

export default logger;

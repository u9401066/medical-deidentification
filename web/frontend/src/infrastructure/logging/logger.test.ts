/**
 * Logger Tests
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { logger, getAllLogs, getLogsByLevel, clearLogs } from './logger';

describe('Logger', () => {
  beforeEach(() => {
    // 清除日誌
    clearLogs();
    // Mock console.log
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  describe('log methods', () => {
    it('should log debug messages', () => {
      logger.debug('Debug message');
      expect(console.log).toHaveBeenCalled();
    });

    it('should log info messages', () => {
      logger.info('Info message');
      expect(console.log).toHaveBeenCalled();
    });

    it('should log warn messages', () => {
      logger.warn('Warning message');
      expect(console.log).toHaveBeenCalled();
    });

    it('should log error messages', () => {
      logger.error('Error message');
      expect(console.log).toHaveBeenCalled();
    });

    it('should log with context', () => {
      logger.info('Message with context', { key: 'value' });
      expect(console.log).toHaveBeenCalled();
    });
  });

  describe('getAllLogs', () => {
    it('should return all stored logs', () => {
      logger.info('First');
      logger.error('Second');

      const logs = getAllLogs();
      expect(logs.length).toBe(2);
    });

    it('should return empty array when no logs', () => {
      const logs = getAllLogs();
      expect(logs).toEqual([]);
    });
  });

  describe('getLogsByLevel', () => {
    it('should filter logs by level', () => {
      logger.info('Info 1');
      logger.error('Error 1');
      logger.info('Info 2');

      const infoLogs = getLogsByLevel('INFO');
      expect(infoLogs.length).toBe(2);

      const errorLogs = getLogsByLevel('ERROR');
      expect(errorLogs.length).toBe(1);
    });
  });

  describe('clearLogs', () => {
    it('should clear all logs', () => {
      logger.info('Message');
      expect(getAllLogs().length).toBe(1);

      clearLogs();
      expect(getAllLogs().length).toBe(0);
    });
  });
});

/**
 * File Entity Tests
 */
import { describe, it, expect } from 'vitest';
import {
  createUploadedFile,
  formatFileSize,
  getFileExtension,
  isSupportedFileType,
} from './File';

describe('File Entity', () => {
  const mockFileData = {
    file_id: 'file-123',
    filename: 'test-data.xlsx',
    size: 1024 * 1024, // 1 MB
    upload_time: '2026-01-14T10:00:00Z',
    file_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    preview_available: true,
    status: 'pending',
  };

  describe('createUploadedFile', () => {
    it('should create a File entity from API response', () => {
      const file = createUploadedFile(mockFileData);

      expect(file.id).toBe('file-123');
      expect(file.filename).toBe('test-data.xlsx');
      expect(file.size).toBe(1024 * 1024);
      expect(file.uploadTime).toBeInstanceOf(Date);
      expect(file.previewAvailable).toBe(true);
      expect(file.status).toBe('pending');
    });

    it('should fallback to id when file_id is not present', () => {
      const data = { ...mockFileData, file_id: undefined, id: 'fallback-id' };
      const file = createUploadedFile(data);
      expect(file.id).toBe('fallback-id');
    });

    it('should default status to pending', () => {
      const data = { ...mockFileData, status: undefined };
      const file = createUploadedFile(data);
      expect(file.status).toBe('pending');
    });
  });

  describe('formatFileSize', () => {
    it('should format 0 bytes', () => {
      expect(formatFileSize(0)).toBe('0 B');
    });

    it('should format bytes', () => {
      expect(formatFileSize(500)).toBe('500 B');
    });

    it('should format kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1536)).toBe('1.5 KB');
    });

    it('should format megabytes', () => {
      expect(formatFileSize(1024 * 1024)).toBe('1 MB');
      expect(formatFileSize(1.5 * 1024 * 1024)).toBe('1.5 MB');
    });

    it('should format gigabytes', () => {
      expect(formatFileSize(1024 * 1024 * 1024)).toBe('1 GB');
    });
  });

  describe('getFileExtension', () => {
    it('should extract file extension', () => {
      expect(getFileExtension('test.xlsx')).toBe('xlsx');
      expect(getFileExtension('data.CSV')).toBe('csv');
      expect(getFileExtension('report.json')).toBe('json');
    });

    it('should handle files with multiple dots', () => {
      expect(getFileExtension('my.data.file.xlsx')).toBe('xlsx');
    });

    it('should return empty string for files without extension', () => {
      expect(getFileExtension('noextension')).toBe('');
    });
  });

  describe('isSupportedFileType', () => {
    it('should return true for supported file types', () => {
      expect(isSupportedFileType('test.xlsx')).toBe(true);
      expect(isSupportedFileType('data.csv')).toBe(true);
      expect(isSupportedFileType('config.json')).toBe(true);
      expect(isSupportedFileType('notes.txt')).toBe(true);
    });

    it('should return false for unsupported file types', () => {
      expect(isSupportedFileType('image.png')).toBe(false);
      expect(isSupportedFileType('document.pdf')).toBe(false);
      expect(isSupportedFileType('script.py')).toBe(false);
    });
  });
});

/**
 * @fileoverview Tests for API client utilities
 * Tests error handling, request formatting, and type safety
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { analysisApi, handleApiError } from '@/lib/api';
import type { Analysis } from '@/types';

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: vi.fn(),
      get: vi.fn(),
    })),
  },
}));

// Mock the api instance directly
const mockApi = {
  post: vi.fn(),
  get: vi.fn(),
};

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual('@/lib/api');
  return {
    ...actual,
    // Override the api instance used internally
  };
});

// Create a simpler mock for the axios instance
vi.doMock('@/lib/api', async () => {
  const { handleApiError } = await vi.importActual('@/lib/api');
  
  return {
    analysisApi: {
      uploadImages: vi.fn(),
      getAnalysis: vi.fn(),
      getAnalysisStatus: vi.fn(),
    },
    handleApiError,
  };
});

const { analysisApi } = await import('@/lib/api');
const mockedAnalysisApi = vi.mocked(analysisApi);

describe('analysisApi', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('uploadImages', () => {
    it('should upload images and return analysis data', async () => {
      const mockAnalysis: Analysis = {
        id: 1,
        status: 'QUEUED',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      const mockResponse = { data: mockAnalysis };
      mockedAxios.post.mockResolvedValue(mockResponse);

      const file1 = new File(['test'], 'palm1.jpg', { type: 'image/jpeg' });
      const file2 = new File(['test'], 'palm2.jpg', { type: 'image/jpeg' });
      const files = [file1, file2];

      const result = await analysisApi.uploadImages(files);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/analyses/upload',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      expect(result).toEqual(mockAnalysis);
    });

    it('should handle upload errors gracefully', async () => {
      const errorMessage = 'Upload failed';
      mockedAxios.post.mockRejectedValue(new Error(errorMessage));

      const file = new File(['test'], 'palm.jpg', { type: 'image/jpeg' });
      
      await expect(analysisApi.uploadImages([file])).rejects.toThrow(errorMessage);
    });
  });

  describe('getAnalysis', () => {
    it('should fetch analysis by ID', async () => {
      const mockAnalysis: Analysis = {
        id: 1,
        status: 'COMPLETED',
        summary: 'Your palm shows strong life lines...',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      const mockResponse = { data: mockAnalysis };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await analysisApi.getAnalysis('1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/analyses/1');
      expect(result).toEqual(mockAnalysis);
    });
  });

  describe('getAnalysisStatus', () => {
    it('should fetch analysis status', async () => {
      const mockStatus = { 
        status: 'processing', 
        progress: 50,
        result: null 
      };

      const mockResponse = { data: mockStatus };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await analysisApi.getAnalysisStatus('1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/analyses/1/status');
      expect(result).toEqual(mockStatus);
    });
  });
});

describe('handleApiError', () => {
  it('should handle server response errors', () => {
    const error = {
      response: {
        data: {
          detail: 'Invalid file format'
        }
      }
    };

    const result = handleApiError(error);
    expect(result).toBe('Error: Invalid file format');
  });

  it('should handle network errors', () => {
    const error = {
      request: {}
    };

    const result = handleApiError(error);
    expect(result).toBe('Network error: Unable to connect to server');
  });

  it('should handle generic errors', () => {
    const error = new Error('Something went wrong');

    const result = handleApiError(error);
    expect(result).toBe('Error: Something went wrong');
  });

  it('should handle server errors without detail', () => {
    const error = {
      response: {
        data: {}
      }
    };

    const result = handleApiError(error);
    expect(result).toBe('Error: Server error occurred');
  });
});
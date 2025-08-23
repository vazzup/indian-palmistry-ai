/**
 * @fileoverview API client for Indian Palmistry AI frontend
 * Provides typed axios client with error handling for backend integration
 */

import axios from 'axios';
import type { Analysis } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Configured axios instance for Indian Palmistry AI backend
 * Features timeout, base URL configuration, and default headers
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Analysis API client with typed endpoints
 * Handles palm image upload and analysis retrieval
 */
export const analysisApi = {
  /**
   * Upload palm images for AI analysis
   * @param files - Array of image files (typically left and right palms)
   * @returns Promise resolving to Analysis object with job details
   * @throws Error with user-friendly message on upload failure
   */
  async uploadImages(files: File[]): Promise<Analysis> {
    const formData = new FormData();
    
    files.forEach((file, index) => {
      formData.append(`file${index}`, file);
    });

    try {
      const response = await api.post('/api/v1/analyses/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data;
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    }
  },

  /**
   * Get analysis results by ID
   * @param id - Analysis ID returned from upload
   * @returns Promise resolving to complete Analysis object
   */
  async getAnalysis(id: string): Promise<Analysis> {
    try {
      const response = await api.get(`/api/v1/analyses/${id}`);
      return response.data;
    } catch (error) {
      console.error('Get analysis failed:', error);
      throw error;
    }
  },

  /**
   * Get analysis processing status for background jobs
   * @param id - Analysis ID to check status for
   * @returns Promise with job status, result, and error information
   */
  async getAnalysisStatus(id: string): Promise<{ status: string; result?: any; error?: string }> {
    try {
      const response = await api.get(`/api/v1/analyses/${id}/status`);
      return response.data;
    } catch (error) {
      console.error('Get analysis status failed:', error);
      throw error;
    }
  },
};

/**
 * Converts API errors to user-friendly error messages
 * @param error - Axios error object or any error
 * @returns Human-readable error message for display to users
 */
export function handleApiError(error: any): string {
  if (error.response) {
    // Server responded with error status
    const message = error.response.data?.detail || error.response.data?.message || 'Server error occurred';
    return `Error: ${message}`;
  } else if (error.request) {
    // Request made but no response received
    return 'Network error: Unable to connect to server';
  } else {
    // Something else happened
    return `Error: ${error.message}`;
  }
}
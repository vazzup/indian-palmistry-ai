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
  withCredentials: true, // Enable cookies for session management
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
    
    // Backend expects 'left_image' and 'right_image' fields
    if (files.length > 0) {
      formData.append('left_image', files[0]);
    }
    if (files.length > 1) {
      formData.append('right_image', files[1]);
    }

    try {
      const response = await api.post('/api/v1/analyses/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data;
    } catch (error) {
      console.error('Upload failed:', error);
      throw new Error(handleApiError(error));
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

  /**
   * Get analysis summary (public endpoint - no authentication required)
   * @param id - Analysis ID to get summary for
   * @returns Promise resolving to analysis summary data
   */
  async getAnalysisSummary(id: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/analyses/${id}/summary`);
      return response.data;
    } catch (error) {
      console.error('Get analysis summary failed:', error);
      throw error;
    }
  },
};

/**
 * Authentication API client for login, register, and user management
 */
export const authApi = {
  /**
   * User registration
   */
  async register(data: { email: string; password: string; name: string }): Promise<any> {
    try {
      const response = await api.post('/api/v1/auth/register', {
        email: data.email,
        password: data.password,
        name: data.name
      });
      return response.data;
    } catch (error) {
      console.error('Registration failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * User login
   */
  async login(data: { email: string; password: string }): Promise<any> {
    try {
      const response = await api.post('/api/v1/auth/login', {
        email: data.email,
        password: data.password
      });
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * User logout
   */
  async logout(): Promise<void> {
    try {
      await api.post('/api/v1/auth/logout');
    } catch (error) {
      console.error('Logout failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<any> {
    try {
      const response = await api.get('/api/v1/auth/me');
      return response.data;
    } catch (error: any) {
      // Handle 401 gracefully - user is not authenticated
      if (error.response?.status === 401) {
        return null;
      }
      console.error('Get current user failed:', error);
      throw new Error(handleApiError(error));
    }
  }
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
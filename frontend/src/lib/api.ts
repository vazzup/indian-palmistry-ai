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

// Response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.log(`API Request failed: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    });

    // Handle 401 Unauthorized errors by clearing local auth state
    if (error.response?.status === 401) {
      console.log('API: Received 401 Unauthorized - clearing local auth state');
      // Only clear auth state if we're in the browser (not SSR)
      if (typeof window !== 'undefined') {
        // Import auth store dynamically to avoid SSR issues
        import('@/lib/auth').then(({ useAuthStore }) => {
          console.log('API: Clearing auth state due to 401 error');
          // Clear local auth state without calling server logout
          // since server already rejected the session
          useAuthStore.setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        }).catch(console.error);
      }
    }
    return Promise.reject(error);
  }
);

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
  async getAnalysisStatus(id: string): Promise<{ status: string; result?: any; error_message?: string }> {
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

  /**
   * Delete an analysis and all associated data
   * @param id - Analysis ID to delete
   * @returns Promise resolving to success message
   * @throws Error if user doesn't have permission or analysis not found
   */
  async deleteAnalysis(id: string): Promise<{ message: string }> {
    try {
      const response = await api.delete(`/api/v1/analyses/${id}`);
      return response.data;
    } catch (error) {
      console.error('Delete analysis failed:', error);
      throw error;
    }
  },

  /**
   * Associate an anonymous analysis with the current authenticated user
   * @param id - Analysis ID to associate
   * @returns Promise resolving to success message
   * @throws Error if analysis not found or already associated
   */
  async associateAnalysis(id: string): Promise<{ message: string }> {
    try {
      const response = await api.put(`/api/v1/analyses/${id}/associate`);
      return response.data;
    } catch (error) {
      console.error('Associate analysis failed:', error);
      throw error;
    }
  },
};

/**
 * Export the base API client for direct use
 */
export { api };

/**
 * Authentication API client for login, register, and user management
 */
export const authApi = {
  /**
   * User registration
   */
  async register(data: { email: string; password: string; name: string; age: number; gender: string }): Promise<any> {
    try {
      const response = await api.post('/api/v1/auth/register', {
        email: data.email,
        password: data.password,
        name: data.name,
        age: data.age,
        gender: data.gender
      });
      
      // Log the raw API response for debugging
      
      // Extract user from the AuthResponse structure
      // Backend returns: { success, message, user: {...}, csrf_token }
      if (response.data && response.data.user) {
        return response.data.user;
      } else {
        throw new Error('Invalid response format: missing user data');
      }
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
      
      // Log the raw API response for debugging
      
      // Extract user from the LoginResponse structure
      // Backend returns: { success, message, user: {...}, csrf_token, session_expires }
      if (response.data && response.data.user) {
        return response.data.user;
      } else {
        throw new Error('Invalid response format: missing user data');
      }
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
      
      // Log the response for debugging
      
      // /me endpoint returns UserResponse directly (not wrapped)
      return response.data;
    } catch (error: any) {
      // Handle 401 gracefully - user is not authenticated
      if (error.response?.status === 401) {
        // Return null to indicate no authenticated user, but don't throw
        // This allows checkAuth to handle the null return gracefully
        return null;
      }
      console.error('Get current user failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get CSRF token for security
   */
  async getCSRFToken(): Promise<string> {
    try {
      console.log('authApi.getCSRFToken: Requesting CSRF token...');
      const response = await api.get('/api/v1/auth/csrf-token');
      console.log('authApi.getCSRFToken: Success, got token');
      return response.data.csrf_token;
    } catch (error: any) {
      console.error('authApi.getCSRFToken: Failed with error:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        detail: error?.response?.data?.detail,
        message: error?.message
      });
      // Return empty string if CSRF is not available
      return '';
    }
  },

  /**
   * Complete user profile with age and gender (for OAuth users)
   */
  async completeProfile(data: { age: number; gender: string }): Promise<any> {
    try {
      const response = await api.post('/api/v1/auth/complete-profile', {
        age: data.age,
        gender: data.gender
      });

      // Return the updated user data
      return response.data;
    } catch (error) {
      console.error('Profile completion failed:', error);
      throw new Error(handleApiError(error));
    }
  }
};

/**
 * Dashboard API client for analytics and statistics
 */
export const dashboardApi = {
  /**
   * Get user dashboard overview with stats and recent activity
   */
  async getDashboard(): Promise<{
    overview: {
      total_analyses: number;
      completed_analyses: number;
      total_conversations: number;
      success_rate: number;
    };
    recent_activity: any[];
    analytics: any;
  }> {
    try {
      const response = await api.get('/api/v1/enhanced/dashboard');
      // Extract data from the success wrapper
      return response.data.data || response.data;
    } catch (error: any) {
      console.error('Get dashboard failed:', error);
      
      // Handle authentication errors gracefully
      if (error.response?.status === 401) {
        throw new Error('Please log in to view your dashboard');
      }
      
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get paginated list of user analyses
   */
  async getAnalyses(params?: {
    page?: number;
    limit?: number;
    status?: string;
    sort?: string;
  }): Promise<{
    analyses: any[];
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.status) queryParams.append('status', params.status);
      if (params?.sort) queryParams.append('sort', params.sort);

      const response = await api.get(`/api/v1/analyses/?${queryParams.toString()}`);
      // The basic analyses endpoint returns data directly, not wrapped
      return response.data;
    } catch (error) {
      console.error('Get analyses failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get detailed dashboard statistics
   */
  async getDashboardStatistics(): Promise<any> {
    try {
      const response = await api.get('/api/v1/enhanced/dashboard/statistics');
      // Extract data from the success wrapper
      return response.data.data || response.data;
    } catch (error: any) {
      console.error('Get dashboard statistics failed:', error);
      
      // Handle authentication errors gracefully
      if (error.response?.status === 401) {
        throw new Error('Please log in to view statistics');
      }
      
      throw new Error(handleApiError(error));
    }
  },
};

/**
 * Conversations API client for chat management and message history
 */
export const conversationsApi = {
  /**
   * Get the single conversation for a specific analysis
   */
  async getAnalysisConversation(analysisId: string): Promise<any | null> {
    try {
      const response = await api.get(`/api/v1/analyses/${analysisId}/conversations/`);
      return response.data;
    } catch (error: any) {
      // Handle 404 gracefully - analysis has no conversation yet
      if (error.response?.status === 404) {
        return null;
      }
      console.error('Get analysis conversation failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get all conversations for the current user (legacy method - now returns conversations across all analyses)
   * @deprecated Use getAnalysisConversation for specific analysis conversations
   */
  async getUserConversations(params?: {
    page?: number;
    limit?: number;
    analysis_id?: string;
    sort?: string;
  }): Promise<{
    conversations: any[];
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.analysis_id) queryParams.append('analysis_id', params.analysis_id);
      if (params?.sort) queryParams.append('sort', params.sort);

      const response = await api.get(`/api/v1/conversations/?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Get conversations failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get messages for a specific conversation
   */
  async getConversationMessages(analysisId: string, conversationId: string, params?: {
    page?: number;
    per_page?: number;
  }): Promise<{
    messages: any[];
    total: number;
    page: number;
    per_page: number;
    has_more: boolean;
    conversation_id: number;
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.per_page) queryParams.append('per_page', params.per_page.toString());
      
      const queryString = queryParams.toString();
      const url = `/api/v1/analyses/${analysisId}/conversations/${conversationId}/messages${queryString ? `?${queryString}` : ''}`;

      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Get conversation messages failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Create a new conversation for an analysis (or get existing one if it already exists)
   */
  async createConversation(data: {
    analysis_id: number;
    title: string;
  }): Promise<any> {
    try {
      const response = await api.post(`/api/v1/analyses/${data.analysis_id}/conversations/`, {
        title: data.title
      });
      return response.data;
    } catch (error) {
      console.error('Create conversation failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Start a new conversation with initial reading and first question
   */
  async startConversation(analysisId: string, firstQuestion: string): Promise<any> {
    try {
      // Get CSRF token for security
      console.log('startConversation: Getting CSRF token...');
      const csrfToken = await authApi.getCSRFToken();
      console.log('startConversation: Got CSRF token:', csrfToken ? 'SUCCESS' : 'EMPTY');
      
      console.log('startConversation: Making API request with token:', csrfToken ? 'present' : 'empty');
      const response = await api.post(`/api/v1/analyses/${analysisId}/conversations/start`, {
        message: firstQuestion
      }, {
        headers: {
          'X-CSRF-Token': csrfToken
        }
      });
      console.log('startConversation: API request successful');
      return response.data;
    } catch (error: any) {
      console.error('startConversation: Failed with error:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        detail: error?.response?.data?.detail,
        url: error?.config?.url
      });
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Send a message in a conversation and get AI response
   */
  async sendMessage(analysisId: string, conversationId: string, content: string): Promise<any> {
    try {
      // Get CSRF token for security
      const csrfToken = await authApi.getCSRFToken();
      
      const response = await api.post(`/api/v1/analyses/${analysisId}/conversations/${conversationId}/talk`, {
        message: content
      }, {
        headers: {
          'X-CSRF-Token': csrfToken
        }
      });
      return response.data;
    } catch (error) {
      console.error('Send message failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Delete a conversation
   */
  async deleteConversation(analysisId: string, conversationId: string): Promise<void> {
    try {
      await api.delete(`/api/v1/analyses/${analysisId}/conversations/${conversationId}`);
    } catch (error) {
      console.error('Delete conversation failed:', error);
      throw new Error(handleApiError(error));
    }
  },
};

/**
 * Cache management API client for debugging and maintenance
 */
export const cacheApi = {
  /**
   * Get cache debug information
   * Shows current cache state and statistics
   */
  async getCacheDebug(): Promise<{
    total_keys: number;
    user_keys: Record<string, number>;
    pattern_breakdown: Record<string, number>;
    memory_usage?: string;
    cache_stats: {
      hits: number;
      misses: number;
      hit_ratio: number;
    };
  }> {
    try {
      const response = await api.get('/api/v1/cache/debug');
      return response.data;
    } catch (error) {
      console.error('Get cache debug failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Refresh cache for current user
   * Invalidates all user-specific cached data
   */
  async refreshCache(): Promise<{
    success: boolean;
    invalidated_keys: number;
    message: string;
  }> {
    try {
      const response = await api.post('/api/v1/cache/refresh');
      return response.data;
    } catch (error) {
      console.error('Cache refresh failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Validate cache consistency
   * Checks for data inconsistencies between cache and database
   */
  async validateCacheConsistency(): Promise<{
    consistent: boolean;
    inconsistencies: Array<{
      key: string;
      issue: string;
      cached_value?: any;
      db_value?: any;
    }>;
    total_checked: number;
    recommendations: string[];
  }> {
    try {
      const response = await api.get('/api/v1/cache/validate-consistency');
      return response.data;
    } catch (error) {
      console.error('Cache consistency validation failed:', error);
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Force refresh specific cache pattern
   * @param pattern - Cache key pattern to refresh (e.g., 'dashboard:*', 'analyses:*')
   */
  async refreshCachePattern(pattern: string): Promise<{
    success: boolean;
    invalidated_keys: number;
    pattern: string;
    message: string;
  }> {
    try {
      const response = await api.post('/api/v1/cache/refresh', { pattern });
      return response.data;
    } catch (error) {
      console.error('Pattern cache refresh failed:', error);
      throw new Error(handleApiError(error));
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
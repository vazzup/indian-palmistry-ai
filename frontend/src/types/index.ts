// Core API types matching FastAPI backend

export interface User {
  id: number;
  email: string;
  name: string;
  picture?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Analysis {
  id: number;
  user_id?: number;
  left_image_path?: string;
  right_image_path?: string;
  left_thumbnail_path?: string;
  right_thumbnail_path?: string;
  summary?: string;
  full_report?: string;
  // Additional analysis fields returned from OpenAI Responses API
  key_features?: string[];
  strengths?: string[];
  guidance?: string[];
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  job_id?: string;
  error_message?: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  tokens_used?: number;
  cost?: number;
  created_at: string;
  updated_at: string;
  // New conversation mode fields
  conversation_mode: 'analysis' | 'chat';
  conversation_id?: number;
}

export interface Conversation {
  id: number;
  analysis_id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'USER' | 'ASSISTANT';
  content: string;
  message_type: 'INITIAL_READING' | 'USER_QUESTION' | 'AI_RESPONSE';
  analysis_data?: Record<string, any>;
  tokens_used?: number;
  cost?: number;
  created_at: string;
}

// API Response types for conversation endpoints
export interface TalkResponse {
  user_message: Message;
  assistant_message: Message;
  tokens_used: number;
  cost: number;
}

export interface InitialConversationResponse {
  conversation: Conversation;
  initial_message: Message;
  user_message: Message;
  assistant_message: Message;
  tokens_used: number;
  cost: number;
}

export interface JobStatus {
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress?: number;
  error?: string;
  result?: any;
}

// API Response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// Authentication types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  user: User;
  message: string;
}

// Form validation types
export interface FormErrors {
  [key: string]: string | undefined;
}

// Cultural design system types
export type CulturalColor = 
  | 'saffron'
  | 'turmeric' 
  | 'marigold'
  | 'vermillion'
  | 'sandalwood'
  | 'lotus';

export type ComponentSize = 'sm' | 'md' | 'lg' | 'xl';
export type ComponentVariant = 'default' | 'outline' | 'ghost' | 'destructive';

// Upload types
export interface UploadProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
}

// Dashboard types
export interface DashboardStats {
  total_analyses: number;
  completed_analyses: number;
  total_conversations: number;
  total_messages: number;
  total_cost: number;
}

export interface UserPreferences {
  theme: 'light' | 'dark';
  notifications: boolean;
  language: string;
  privacy_level: 'public' | 'private';
}
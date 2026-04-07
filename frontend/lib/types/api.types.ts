export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  timestamp: string;
}

export interface ApiError {
  status: 'error';
  message: string;
  code?: string;
}

import { Response } from 'express';

export interface ApiSuccessResponse<T = any> {
  success: true;
  message: string;
  data: T;
  pagination?: {
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  };
}

export interface ApiErrorResponse {
  success: false;
  error: string;
  details?: any;
}

export type ApiResponse<T = any> = ApiSuccessResponse<T> | ApiErrorResponse;

/**
 * Send standardized success response
 */
export function sendSuccess<T>(
  res: Response,
  data: T,
  message: string = 'Success',
  statusCode: number = 200,
  pagination?: ApiSuccessResponse['pagination']
): void {
  const response: ApiSuccessResponse<T> = {
    success: true,
    message,
    data,
  };
  
  if (pagination) {
    response.pagination = pagination;
  }
  
  res.status(statusCode).json(response);
}

/**
 * Send standardized error response
 */
export function sendError(
  res: Response,
  error: string,
  statusCode: number = 400,
  details?: any
): void {
  const response: ApiErrorResponse = {
    success: false,
    error,
  };
  
  if (details) {
    response.details = details;
  }
  
  res.status(statusCode).json(response);
}

/**
 * Send paginated response
 */
export function sendPaginated<T>(
  res: Response,
  data: T[],
  total: number,
  page: number,
  limit: number,
  message: string = 'Data retrieved successfully'
): void {
  sendSuccess(
    res,
    data,
    message,
    200,
    {
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    }
  );
}

import { PaginationQuery } from '../types';

export interface PaginationResult {
  page: number;
  limit: number;
  skip: number;
  sort: Record<string, 1 | -1>;
}

export const parsePagination = (query: PaginationQuery): PaginationResult => {
  const page = Math.max(1, parseInt(query.page || '1', 10));
  const limit = Math.min(100, Math.max(1, parseInt(query.limit || '10', 10)));
  const skip = (page - 1) * limit;
  const sortField = query.sort || 'createdAt';
  const sortOrder: 1 | -1 = query.order === 'asc' ? 1 : -1;
  return { page, limit, skip, sort: { [sortField]: sortOrder } };
};

export const buildPaginationMeta = (total: number, page: number, limit: number) => ({
  page,
  limit,
  total,
  totalPages: Math.ceil(total / limit),
});

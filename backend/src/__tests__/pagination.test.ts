import { parsePagination, buildPaginationMeta } from '../utils/pagination';

describe('Pagination Utilities', () => {
  describe('parsePagination', () => {
    it('returns defaults when no query params', () => {
      const result = parsePagination({});
      expect(result.page).toBe(1);
      expect(result.limit).toBe(10);
      expect(result.skip).toBe(0);
      expect(result.sort).toEqual({ createdAt: -1 });
    });

    it('parses page and limit correctly', () => {
      const result = parsePagination({ page: '3', limit: '25' });
      expect(result.page).toBe(3);
      expect(result.limit).toBe(25);
      expect(result.skip).toBe(50);
    });

    it('clamps limit to max 100', () => {
      const result = parsePagination({ limit: '9999' });
      expect(result.limit).toBe(100);
    });

    it('clamps page minimum to 1', () => {
      const result = parsePagination({ page: '-5' });
      expect(result.page).toBe(1);
    });

    it('parses ascending sort order', () => {
      const result = parsePagination({ sort: 'name', order: 'asc' });
      expect(result.sort).toEqual({ name: 1 });
    });

    it('parses descending sort order', () => {
      const result = parsePagination({ sort: 'date', order: 'desc' });
      expect(result.sort).toEqual({ date: -1 });
    });
  });

  describe('buildPaginationMeta', () => {
    it('calculates totalPages correctly', () => {
      const meta = buildPaginationMeta(100, 1, 10);
      expect(meta.totalPages).toBe(10);
      expect(meta.total).toBe(100);
      expect(meta.page).toBe(1);
      expect(meta.limit).toBe(10);
    });

    it('rounds up totalPages', () => {
      const meta = buildPaginationMeta(101, 1, 10);
      expect(meta.totalPages).toBe(11);
    });

    it('returns 0 totalPages for empty results', () => {
      const meta = buildPaginationMeta(0, 1, 10);
      expect(meta.totalPages).toBe(0);
    });

    it('handles single page correctly', () => {
      const meta = buildPaginationMeta(5, 1, 10);
      expect(meta.totalPages).toBe(1);
    });
  });
});

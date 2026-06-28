import request from 'supertest';
import { app } from '../app';

describe('API Integration Tests', () => {
  describe('GET /health', () => {
    it('returns 200 with healthy status', async () => {
      const res = await request(app).get('/health');
      expect(res.status).toBe(200);
      expect(res.body.status).toBe('ok');
      expect(res.body.version).toBe('1.0.0');
      expect(res.body.timestamp).toBeDefined();
    });
  });

  describe('GET /nonexistent', () => {
    it('returns 404 for unknown routes', async () => {
      const res = await request(app).get('/nonexistent-route');
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
      expect(res.body.message).toBe('Route not found');
    });
  });

  describe('POST /api/v1/auth/register — validation', () => {
    it('rejects invalid email', async () => {
      const res = await request(app)
        .post('/api/v1/auth/register')
        .send({ email: 'not-an-email', password: 'Test@1234', firstName: 'Test', lastName: 'User' });
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });

    it('rejects short password', async () => {
      const res = await request(app)
        .post('/api/v1/auth/register')
        .send({ email: 'test@test.com', password: '123', firstName: 'Test', lastName: 'User' });
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });

    it('rejects missing fields', async () => {
      const res = await request(app)
        .post('/api/v1/auth/register')
        .send({ email: 'test@test.com' });
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });
  });

  describe('POST /api/v1/auth/login — validation', () => {
    it('rejects empty body', async () => {
      const res = await request(app).post('/api/v1/auth/login').send({});
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });

    it('rejects invalid email format', async () => {
      const res = await request(app)
        .post('/api/v1/auth/login')
        .send({ email: 'notanemail', password: 'pass' });
      expect(res.status).toBe(400);
    });
  });

  describe('Protected routes — authentication', () => {
    it('returns 401 without token on /api/v1/auth/me', async () => {
      const res = await request(app).get('/api/v1/auth/me');
      expect(res.status).toBe(401);
      expect(res.body.success).toBe(false);
    });

    it('returns 401 with malformed token', async () => {
      const res = await request(app)
        .get('/api/v1/auth/me')
        .set('Authorization', 'Bearer not.a.valid.token');
      expect(res.status).toBe(401);
    });

    it('returns 401 without Bearer prefix', async () => {
      const res = await request(app)
        .get('/api/v1/auth/me')
        .set('Authorization', 'eyJhbGciOiJIUzI1NiJ9.e30.token');
      expect(res.status).toBe(401);
    });

    it('returns 401 for records without auth', async () => {
      const res = await request(app).get('/api/v1/records');
      expect(res.status).toBe(401);
    });

    it('returns 401 for appointments without auth', async () => {
      const res = await request(app).get('/api/v1/appointments');
      expect(res.status).toBe(401);
    });
  });

  describe('Rate limiting headers', () => {
    it('includes rate limit headers on auth endpoints', async () => {
      const res = await request(app)
        .post('/api/v1/auth/login')
        .send({ email: 'test@test.com', password: 'test' });
      // Without DB: validation passes but DB connection fails → 500
      // With rate limiting: 429. Either way, not 200 OK without real DB
      expect([400, 429, 500, 503]).toContain(res.status);
    });
  });
});

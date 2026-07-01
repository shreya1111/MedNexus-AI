# Phase 5C Testing Guide

## Overview

Complete testing guide for all integrated features in MedNexus-AI.

**Status**: Phase 5C Complete (100%)  
**Date**: January 2025

---

## Prerequisites

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations (if needed)
alembic upgrade head

# Start backend server
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env: VITE_API_URL=http://localhost:8000

# Start development server
npm run dev
```

---

## Testing Checklist

### 1. Authentication ✅

**Test: User Registration**
1. Navigate to `/register`
2. Enter: name, email, password
3. Submit form
4. Verify redirect to `/login`
5. Check toast notification

**Test: User Login**
1. Navigate to `/login`
2. Enter valid credentials
3. Submit form
4. Verify redirect to `/dashboard`
5. Check token stored in localStorage
6. Check user info in navbar

**Test: Token Refresh**
1. Login successfully
2. Wait for token to expire (or manually expire it)
3. Make an API request
4. Verify automatic token refresh
5. Verify request succeeds after refresh

**Test: Logout**
1. Click user menu in navbar
2. Click "Logout"
3. Verify redirect to `/login`
4. Verify tokens cleared from localStorage
5. Verify cannot access protected routes

**Test: Protected Routes**
1. Logout
2. Try to access `/dashboard`
3. Verify redirect to `/login`
4. Login and verify access granted

---

### 2. AI Medical Chat ✅

**Test: Send Message**
1. Navigate to `/chat`
2. Type a medical question: "What are symptoms of diabetes?"
3. Click send or press Enter
4. Verify user message appears immediately (optimistic update)
5. Verify AI response appears with confidence score
6. Verify citations displayed
7. Check follow-up questions

**Test: Session Management**
1. Click "New Conversation"
2. Verify new session created
3. Send messages in new session
4. Switch between sessions in sidebar
5. Verify messages persist correctly

**Test: Chat History**
1. Refresh page
2. Verify previous sessions load
3. Click on a session
4. Verify all messages display correctly

**Test: Delete Session**
1. Click delete icon on a session
2. Confirm deletion
3. Verify session removed from list
4. Verify database record deleted

---

### 3. Dashboard Analytics ✅

**Test: Dashboard Metrics**
1. Navigate to `/dashboard`
2. Verify all metric cards display:
   - Total Conversations
   - Average Confidence
   - Response Latency
   - Knowledge Base Size
3. Verify numbers are real (not 0 if you have data)
4. Check loading states appear briefly

**Test: Usage Trend**
1. Scroll to trends section
2. Verify chart displays usage over time
3. Check data points are accurate

**Test: Recent Activity**
1. Check recent activity section
2. Verify recent conversations listed
3. Check timestamps are correct

---

### 4. Knowledge Search ✅

**Test: Vector Search**
1. Navigate to `/search`
2. Enter query: "heart disease treatment"
3. Click "Search"
4. Verify results appear with:
   - Similarity scores
   - Source documents
   - Relevant text chunks
5. Check top-K filter works (try 5, 10, 20)

**Test: Hybrid Search**
1. Toggle "Hybrid Search"
2. Adjust Vector Weight slider
3. Adjust BM25 Weight slider
4. Perform search
5. Verify results change based on weights

**Test: Search Filters**
1. Try different top-K values
2. Test with different queries
3. Verify empty state when no results

**Test: Search Statistics**
1. Check search stats card
2. Verify total searches count
3. Check average confidence

---

### 5. Medical Reports ✅

**Test: Upload Report**
1. Navigate to `/reports`
2. Click "Upload Report"
3. Select a PDF file (< 10MB)
4. Verify upload toast
5. Verify processing status appears
6. Wait for processing to complete
7. Check status changes to "Processed"

**Test: File Validation**
1. Try uploading file > 10MB → Should show error
2. Try uploading .exe file → Should show error
3. Try uploading valid PDF → Should succeed

**Test: Analyze Report**
1. Click "Analyze" on a processed report
2. Wait for AI analysis (10-30 seconds)
3. Verify dialog opens with:
   - Confidence score
   - Summary
   - Key findings
   - Recommendations
   - Risk factors

**Test: Delete Report**
1. Click trash icon on a report
2. Confirm deletion
3. Verify report removed immediately (optimistic update)
4. Verify file deleted from server

---

### 6. Documents Management ✅

**Test: Upload Document**
1. Navigate to `/documents`
2. Click "Upload Document"
3. Select PDF/TXT/MD/DOC/DOCX file
4. Verify upload and processing
5. Check document statistics update

**Test: Document Statistics**
1. Check stats cards show:
   - Total Documents
   - Processed Documents
   - Pending Documents
   - Total Size

**Test: Download Document**
1. Click "Download" on a document
2. Verify file downloads with correct name
3. Check file content is correct

**Test: Delete Document**
1. Click trash icon
2. Confirm deletion
3. Verify immediate removal from UI
4. Verify stats update

**Test: Pagination**
1. Upload 25+ documents
2. Verify pagination controls appear
3. Click "Next" page
4. Verify page 2 documents load
5. Click "Previous"
6. Verify back to page 1

---

### 7. Profile & Settings ✅

**Test: View Profile**
1. Navigate to `/profile`
2. Verify profile displays:
   - Name
   - Email
   - Role badge
   - Verification status
3. Check statistics cards:
   - Conversations
   - Messages
   - Documents
   - Member Since

**Test: Edit Profile**
1. Click "Edit Profile"
2. Change name
3. Change email
4. Click "Save Changes"
5. Verify toast notification
6. Verify profile updates

**Test: Change Password**
1. Click "Change Password"
2. Enter current password
3. Enter new password
4. Confirm new password
5. Submit
6. Verify success toast
7. Test login with new password

**Test: Settings - Theme**
1. Navigate to `/settings`
2. Change theme to "Dark"
3. Verify UI changes to dark theme
4. Change to "Light"
5. Change to "System"

**Test: Settings - Notifications**
1. Toggle "Enable Notifications"
2. Toggle "Email Notifications"
3. Verify settings save automatically
4. Verify toast confirmation

**Test: Settings - AI Configuration**
1. Change AI Model
2. Change Retrieval Top K (try 3, 10, 15)
3. Change Chunk Size (try 256, 512, 1024)
4. Change Embedding Provider
5. Verify all save successfully

---

### 8. Admin Dashboard ✅

**Note**: Requires admin/superuser account

**Test: System Statistics**
1. Navigate to `/admin` (admin only)
2. Verify system metrics:
   - Total Users
   - Total Conversations
   - System Health
   - Knowledge Base Size

**Test: System Health**
1. Check system health card displays:
   - Overall Status
   - Database Status
   - Vector DB Status
   - AI Service Status
   - CPU Usage %
   - Memory Usage %
   - Disk Usage %

**Test: User Management**
1. Scroll to Users table
2. Verify users listed with:
   - Email
   - Name
   - Role
   - Status badge
   - Last Login
3. Check pagination works

**Test: User Details** (if implemented)
1. Click on a user (if clickable)
2. Verify user details modal/page
3. Check user statistics

---

## API Endpoint Testing

### Using Backend API Docs

1. Navigate to `http://localhost:8000/docs`
2. Test each endpoint manually:

#### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

#### Chat
- `POST /api/v1/chat`
- `GET /api/v1/chat/history`
- `GET /api/v1/chat/history/{session_id}`
- `DELETE /api/v1/chat/history/{session_id}`

#### Dashboard
- `GET /api/v1/dashboard/stats`
- `GET /api/v1/dashboard/stats/{stat_type}`
- `GET /api/v1/dashboard/usage-trend`
- `GET /api/v1/dashboard/health`

#### Search
- `POST /api/v1/search/vector`
- `POST /api/v1/search/hybrid`
- `GET /api/v1/search/stats`

#### Reports
- `POST /api/v1/reports/upload`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{id}`
- `POST /api/v1/reports/{id}/analyze`
- `DELETE /api/v1/reports/{id}`

#### Documents
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{id}`
- `PUT /api/v1/documents/{id}/rename`
- `GET /api/v1/documents/{id}/download`
- `DELETE /api/v1/documents/{id}`
- `GET /api/v1/documents/stats`

#### Profile
- `GET /api/v1/profile`
- `PUT /api/v1/profile`
- `POST /api/v1/profile/password`
- `GET /api/v1/settings`
- `PUT /api/v1/settings`

#### Admin
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/{id}`
- `PUT /api/v1/admin/users/{id}`
- `DELETE /api/v1/admin/users/{id}`
- `GET /api/v1/admin/stats`
- `GET /api/v1/admin/health`
- `GET /api/v1/admin/logs`

---

## Performance Testing

### Load Testing
1. Use tool like Apache Bench or k6
2. Test concurrent users on chat endpoint
3. Test file uploads under load
4. Monitor response times

### Database Queries
1. Check query performance in logs
2. Look for N+1 query problems
3. Verify indexes are used
4. Test with large datasets

### Frontend Performance
1. Check React DevTools Profiler
2. Verify no unnecessary re-renders
3. Check bundle size
4. Test on slow connections

---

## Error Handling Testing

### Network Errors
1. Disconnect internet
2. Try to make requests
3. Verify proper error messages
4. Reconnect and verify retry works

### Validation Errors
1. Submit forms with invalid data
2. Verify field-specific errors show
3. Check error messages are clear

### Server Errors
1. Stop backend server
2. Try to make requests
3. Verify error states display
4. Verify retry buttons work

### 401 Unauthorized
1. Manually expire access token
2. Make authenticated request
3. Verify automatic token refresh
4. If refresh fails, verify redirect to login

### 403 Forbidden
1. Try to access admin endpoint as regular user
2. Verify proper error message
3. Verify no sensitive data leaked

### 404 Not Found
1. Navigate to non-existent route
2. Verify 404 page displays
3. Try to fetch non-existent resource
4. Verify proper error message

---

## Security Testing

### Authentication
- [ ] Passwords are hashed (bcrypt)
- [ ] Tokens expire correctly
- [ ] Refresh tokens are rotated
- [ ] Logout clears all tokens
- [ ] Cannot access protected routes without auth

### Authorization
- [ ] Users can only access their own data
- [ ] Admin endpoints require admin role
- [ ] File access is restricted by user
- [ ] Cannot modify other users' resources

### Input Validation
- [ ] All inputs are validated on backend
- [ ] SQL injection prevented (using ORM)
- [ ] XSS prevented (React auto-escaping)
- [ ] File upload validation (type, size)
- [ ] No sensitive data in error messages

### CORS
- [ ] CORS configured correctly
- [ ] Only allowed origins can access API
- [ ] Credentials included correctly

---

## Mobile Responsiveness Testing

Test on different screen sizes:
1. Desktop (1920x1080)
2. Laptop (1366x768)
3. Tablet (768x1024)
4. Mobile (375x667)

Check:
- [ ] Navigation works on mobile
- [ ] Forms are usable
- [ ] Tables scroll horizontally if needed
- [ ] Buttons are accessible
- [ ] Text is readable
- [ ] Images scale correctly

---

## Browser Compatibility Testing

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

---

## Accessibility Testing

- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Sufficient color contrast
- [ ] Focus indicators visible
- [ ] ARIA labels present
- [ ] Form labels associated correctly

---

## Known Issues & Limitations

1. **Real-time Updates**: Chat doesn't use WebSocket streaming yet
2. **File Upload Progress**: No progress bar for uploads
3. **Offline Support**: No service worker or offline capabilities
4. **Pagination**: Some lists have basic pagination only
5. **Advanced Filters**: Document/report filtering is basic

---

## Success Criteria

All features should:
- [ ] Load without errors
- [ ] Display real data from backend
- [ ] Handle loading states gracefully
- [ ] Show appropriate error messages
- [ ] Support retry on failure
- [ ] Work on mobile devices
- [ ] Be accessible
- [ ] Perform reasonably (< 3s page load)

---

## Reporting Bugs

If you find issues:

1. **Check Console**: Look for JavaScript errors
2. **Check Network**: Look for failed API requests
3. **Check Backend Logs**: Look for server errors
4. **Document Steps**: Write reproduction steps
5. **Include Environment**: Browser, OS, version
6. **Screenshots**: Include if relevant

---

## Next Steps After Testing

1. **Fix Critical Bugs**: Address any blocking issues
2. **Performance Optimization**: Optimize slow queries/pages
3. **Security Audit**: Review authentication and authorization
4. **Documentation**: Update user guides
5. **Deployment**: Prepare for production deployment

---

**Testing Complete**: When all checkboxes are ✅  
**Ready for Production**: After bug fixes and optimization  
**Last Updated**: January 2025

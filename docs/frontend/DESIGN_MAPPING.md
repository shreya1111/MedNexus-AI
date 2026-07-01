# MedNexus-AI Frontend Design Mapping

## Overview

This document maps every Stitch design screen to its corresponding React implementation.

**Design Location**: `docs/designs/stitch_mednexus_ai_clinical_intelligence_platform/`

---

## Design System

### Source
- **Folder**: `clinical_intelligence_narrative/`
- **File**: `DESIGN.md`

### Implementation
- **Theme**: `frontend/src/styles/theme.ts`
- **Colors**: `frontend/tailwind.config.js`
- **Typography**: Tailwind config + CSS custom classes
- **Components**: `frontend/src/components/ui/`

### Key Design Tokens

#### Colors
- **Primary**: `#00d1ff` (Clinical Cyan)
- **Secondary**: `#7000ff` (Neural Purple)
- **Tertiary**: `#feb127` (Amber Alert)
- **Background**: `#0e1417` (Deep Sea)
- **Surface Glass**: `rgba(26, 33, 35, 0.7)` with 12px backdrop blur

#### Typography
- **Font Family**: Inter (UI), JetBrains Mono (Data)
- **Display Large**: 48px/56px, weight 700
- **Headline Medium**: 24px/32px, weight 600
- **Body Large**: 18px/28px, weight 400
- **Label Caps**: 12px/16px, weight 600, letter-spacing 0.05em

#### Spacing
- **XS**: 4px
- **SM**: 8px
- **MD**: 16px
- **LG**: 24px (Gutter)
- **XL**: 32px
- **2XL**: 48px
- **3XL**: 64px

#### Border Radius
- **SM**: 0.125rem (2px)
- **DEFAULT**: 0.25rem (4px)
- **MD**: 0.375rem (6px)
- **LG**: 0.5rem (8px)
- **XL**: 0.75rem (12px)
- **Full**: 9999px

---

## Component Library

### Source
- **Folder**: `component_library_mednexus_ai/`
- **Files**: `code.html`, `screen.png`

### Implementation
- **Location**: `frontend/src/components/ui/`

### Components Identified

#### Core UI Components
- **Button** (`button.tsx`)
  - Primary, Secondary, Ghost, Outline variants
  - Glass effect on hover
  - Active state: scale(0.95)

- **Card** (`card.tsx`)
  - Glass card with backdrop blur
  - Border: 1px rgba(60, 73, 78, 0.5)
  - Hover: cyan glow effect

- **Input** (`input.tsx`)
  - Surface-container-low background
  - Focus ring: cyan at 50% opacity
  - Label-caps for labels

- **Badge** (`badge.tsx`)
  - Pill shape for status
  - Primary, Secondary, Success, Error variants
  - 6px pulse animation for "Live" status

#### Data Display
- **MetricCard** (`metric-card.tsx`)
  - Glass card container
  - Large number display (mono font)
  - Trend indicator with arrow
  - Optional sparkline chart

- **StatCard** (`stat-card.tsx`)
  - Icon + Label + Value
  - Compact glass card
  - Hover effect

- **ChartCard** (`chart-card.tsx`)
  - Card wrapper for Recharts
  - Header with title + period selector
  - Glass background

#### Navigation
- **Sidebar** (`sidebar.tsx`)
  - Fixed left, 256px width (64 units)
  - Glass background
  - Active state: translateX(4px) with cyan accent
  - Icons from Lucide React

- **Navbar** (`navbar.tsx`)
  - Top bar with search + profile
  - Glass background
  - Height: 64px

- **MobileNav** (`mobile-nav.tsx`)
  - Hamburger menu
  - Drawer from left
  - Bottom navigation for mobile

#### Forms
- **SearchBar** (`search-bar.tsx`)
  - Full-width input
  - Magnifying glass icon
  - Keyboard shortcut hint (⌘K)

- **Select** (`select.tsx`)
  - Dropdown with Radix UI
  - Glass background
  - Chevron icon

- **Checkbox** (`checkbox.tsx`)
- **Radio** (`radio-group.tsx`)
- **Switch** (`switch.tsx`)

#### Chat Components
- **ConversationCard** (`conversation-card.tsx`)
  - User message bubble
  - Assistant message bubble
  - Markdown rendering
  - Citation tags
  - Copy button

- **CitationCard** (`citation-card.tsx`)
  - Source reference
  - Similarity score badge
  - Expandable content
  - Link to source

- **TypingIndicator** (`typing-indicator.tsx`)
  - Three dots animation
  - Cyan color

#### Dialogs & Modals
- **Dialog** (`dialog.tsx`)
  - Radix UI Dialog
  - Glass overlay
  - Centered modal

- **AlertDialog** (`alert-dialog.tsx`)
  - Confirmation dialogs
  - Destructive actions

- **Sheet** (`sheet.tsx`)
  - Slide-in panels
  - Mobile drawer

#### Feedback
- **Toast** (`toast.tsx`)
  - Success, Error, Info variants
  - Slide in from top-right
  - Auto-dismiss

- **Skeleton** (`skeleton.tsx`)
  - Loading placeholders
  - Pulse animation

- **EmptyState** (`empty-state.tsx`)
  - Icon + message
  - Call-to-action button

- **ErrorState** (`error-state.tsx`)
  - Error icon + message
  - Retry button

#### Tables
- **Table** (`table.tsx`)
  - Divider lines: outline-variant/30
  - Header: label-caps typography
  - Hover row: surface-container-high

- **Pagination** (`pagination.tsx`)
  - Page numbers
  - Previous/Next buttons
  - Items per page selector

---

## Page Mappings

### 1. Landing Page

#### Design Source
- **Folder**: `landing_page_dark_mode/`
- **Files**: `code.html`, `screen.png`

#### Implementation
- **Page**: `frontend/src/pages/Landing.tsx`
- **Route**: `/`
- **Layout**: `PublicLayout`

#### Sections
1. **Hero** - Display-lg heading, CTA buttons
2. **Features** - 3-column grid of feature cards
3. **Technology** - Architecture diagram
4. **Testimonials** - Carousel (placeholder)
5. **CTA** - Final call-to-action
6. **Footer** - Links + copyright

---

### 2. Authentication Pages

#### Login

**Design Source**: `login_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/auth/Login.tsx`
- **Route**: `/login`
- **Layout**: `AuthLayout`

**Components**:
- Centered glass card
- Email + password inputs
- "Remember me" checkbox
- Primary button
- Link to register + forgot password

#### Register

**Design Source**: `register_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/auth/Register.tsx`
- **Route**: `/register`
- **Layout**: `AuthLayout`

**Components**:
- Full name, email, password, confirm password
- Role selector (Patient, Doctor, Researcher)
- Terms checkbox
- Primary button
- Link to login

#### Forgot Password

**Design Source**: `forgot_password_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/auth/ForgotPassword.tsx`
- **Route**: `/forgot-password`
- **Layout**: `AuthLayout`

**Components**:
- Email input
- Submit button
- Back to login link

#### Reset Password

**Design Source**: `reset_password_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/auth/ResetPassword.tsx`
- **Route**: `/reset-password`
- **Layout**: `AuthLayout`

**Components**:
- New password input
- Confirm password input
- Submit button

#### Email Verification

**Design Source**: `email_verification_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/auth/EmailVerification.tsx`
- **Route**: `/verify-email`
- **Layout**: `AuthLayout`

**Components**:
- Verification code inputs (6 digits)
- Resend code button
- Success state

---

### 3. Dashboard

#### Desktop

**Design Source**: `dashboard_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/Dashboard.tsx`
- **Route**: `/dashboard`
- **Layout**: `DashboardLayout`

**Components**:
1. **Overview Cards** (4 cards)
   - Total Conversations
   - Questions Answered
   - Average Confidence
   - API Usage

2. **Recent Conversations** (Table)
   - Session ID
   - Last Message
   - Confidence
   - Time

3. **Usage Chart** (Line chart)
   - Daily conversation count
   - 7-day trend

4. **Quick Actions** (Card)
   - New Conversation button
   - Search Knowledge button
   - Upload Report button

#### Mobile

**Design Source**: `dashboard_mobile/`

**Implementation**:
- Same page, responsive layout
- Single column
- Hamburger menu
- Bottom navigation

---

### 4. AI Medical Chat

#### Desktop

**Design Source**: `ai_medical_chat_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/Chat.tsx`
- **Route**: `/chat`
- **Layout**: `ChatLayout`

**Layout Structure**:
```
┌─────────────┬────────────────────────────────┐
│  Sidebar    │      Chat Area                 │
│  Sessions   │  ┌──────────────────────────┐  │
│  List       │  │  Messages                │  │
│             │  │  (scrollable)            │  │
│             │  └──────────────────────────┘  │
│             │  ┌──────────────────────────┐  │
│             │  │  Input + Send            │  │
│             │  └──────────────────────────┘  │
└─────────────┴────────────────────────────────┘
```

**Components**:
1. **Conversation Sidebar**
   - Session list
   - New chat button
   - Search sessions

2. **Message List**
   - User messages (right-aligned)
   - Assistant messages (left-aligned)
   - Citations inline
   - Copy button per message
   - Confidence badge

3. **Follow-up Suggestions**
   - Pills below assistant message
   - Click to ask

4. **Input Area**
   - Textarea with auto-resize
   - Send button
   - Character count
   - Keyboard shortcuts (Ctrl+Enter)

5. **Citation Panel** (right sidebar, toggleable)
   - Expandable citation cards
   - Source links
   - Similarity scores

#### Mobile

**Design Source**: `ai_medical_chat_mobile/`

**Implementation**:
- Same page, responsive
- No sidebar (drawer instead)
- Full-width messages
- Bottom input

---

### 5. Knowledge Search

#### Desktop

**Design Source**: `knowledge_search_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/Search.tsx`
- **Route**: `/search`
- **Layout**: `DashboardLayout`

**Components**:
1. **Search Bar** (prominent, top)
   - Full-width input
   - Search icon
   - Filters button

2. **Search Filters** (collapsible)
   - Top-K slider
   - Vector weight slider
   - BM25 weight slider
   - Source filters

3. **Results List**
   - Result cards with:
     - Document excerpt
     - Similarity score
     - Source badge
     - Expand button

4. **Result Detail** (modal or side panel)
   - Full document text
   - Metadata
   - Related documents

#### Mobile

**Design Source**: `knowledge_search_mobile/`

**Implementation**:
- Same page, responsive
- Filters in bottom sheet
- Stacked result cards

---

### 6. Medical Report Analysis

#### Desktop

**Design Source**: `medical_report_analysis_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/Reports.tsx`
- **Route**: `/reports`
- **Layout**: `DashboardLayout`

**Components**:
1. **Upload Area**
   - Drag & drop zone
   - File browser button
   - Supported formats: PDF, TXT, MD
   - Upload progress

2. **Report List** (left panel)
   - Uploaded reports
   - Processing status
   - Click to view

3. **Report Viewer** (main area)
   - Original text (scrollable)
   - AI Summary card
   - Extracted findings
   - Risk indicators
   - Confidence score

4. **Actions**
   - Download summary
   - Regenerate analysis
   - Export as PDF

#### Mobile

**Design Source**: `medical_report_analysis_mobile/`

**Implementation**:
- Same page, responsive
- Single column
- Tabs for Original/Summary

---

### 7. Documents

#### Desktop

**Implementation**:
- **Page**: `frontend/src/pages/Documents.tsx`
- **Route**: `/documents`
- **Layout**: `DashboardLayout`

**Components**:
1. **Document Table**
   - Filename
   - Upload date
   - Size
   - Status
   - Actions (Download, Delete)

2. **Upload Button** (top-right)
   - Opens upload modal

3. **Filters** (top bar)
   - Date range
   - File type
   - Status

---

### 8. User Profile & Settings

#### Profile

**Design Source**: `user_profile_settings_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/Profile.tsx`
- **Route**: `/profile`
- **Layout**: `DashboardLayout`

**Components**:
1. **Profile Card**
   - Avatar upload
   - Full name
   - Email
   - Role badge
   - Edit button

2. **Stats Cards**
   - Total conversations
   - Total questions
   - Join date

#### Settings

**Design Source**: `settings_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/Settings.tsx`
- **Route**: `/settings`
- **Layout**: `DashboardLayout`

**Tabs**:
1. **Account**
   - Change password
   - Email preferences

2. **Appearance**
   - Theme toggle (future: light mode)
   - Font size

3. **Notifications**
   - Email notifications
   - Push notifications

4. **API Keys**
   - Generate API key
   - Revoke keys
   - Usage limits

5. **Privacy**
   - Data export
   - Delete account

#### Mobile

**Design Source**: `settings_mobile/`, `user_profile_mobile/`

**Implementation**:
- Same pages, responsive
- Single column
- Accordion sections

---

### 9. Admin Dashboard

**Design Source**: `admin_dashboard_dark_mode/`

**Implementation**:
- **Page**: `frontend/src/pages/admin/AdminDashboard.tsx`
- **Route**: `/admin`
- **Layout**: `AdminLayout`

**Components**:
1. **Overview Metrics** (4 cards)
   - Total Users
   - Total Conversations
   - System Health
   - API Usage

2. **User Table**
   - Email
   - Role
   - Status
   - Last login
   - Actions (Edit, Disable)

3. **System Health Chart**
   - CPU usage
   - Memory usage
   - Request latency

4. **Activity Log**
   - Recent user actions
   - System events

---

### 10. Error Pages

#### 404 Not Found

**Implementation**:
- **Page**: `frontend/src/pages/NotFound.tsx`
- **Route**: `*` (catch-all)
- **Layout**: `PublicLayout`

**Components**:
- Large 404 text
- Error message
- Back to home button

---

## Layout Hierarchy

```
App (Root)
├── PublicLayout
│   ├── Landing
│   └── NotFound
├── AuthLayout
│   ├── Login
│   ├── Register
│   ├── ForgotPassword
│   ├── ResetPassword
│   └── EmailVerification
├── DashboardLayout
│   ├── Dashboard
│   ├── Search
│   ├── Reports
│   ├── Documents
│   ├── Profile
│   └── Settings
├── ChatLayout
│   └── Chat
└── AdminLayout
    └── AdminDashboard
```

---

## Routing Structure

```typescript
/                       → Landing
/login                  → Login
/register               → Register
/forgot-password        → ForgotPassword
/reset-password         → ResetPassword
/verify-email           → EmailVerification

/dashboard              → Dashboard
/chat                   → Chat
/search                 → Search
/reports                → Reports
/documents              → Documents
/profile                → Profile
/settings               → Settings

/admin                  → AdminDashboard

*                       → NotFound
```

---

## Mobile Responsiveness

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Mobile Adaptations
1. **Sidebar** → Hamburger menu or bottom nav
2. **Multi-column** → Single column
3. **Tables** → Card view
4. **Hover effects** → Touch-friendly buttons
5. **Fixed navbar** → Sticky header

---

## Summary

**Total Screens Mapped**: 21
- Landing: 1
- Auth: 5
- Dashboard: 2 (desktop + mobile)
- Chat: 2 (desktop + mobile)
- Search: 2 (desktop + mobile)
- Reports: 2 (desktop + mobile)
- Documents: 1
- Profile: 2 (profile + settings)
- Admin: 1
- Error: 1

**Total Components**: 40+

**Layouts**: 5

**Routes**: 15+

---

## Implementation Priority

### Phase 1: Foundation (Current)
- [ ] Theme system
- [ ] Base UI components
- [ ] Layouts
- [ ] Routing structure
- [ ] Store architecture
- [ ] API service structure

### Phase 2: Core Pages
- [ ] Landing
- [ ] Authentication pages
- [ ] Dashboard

### Phase 3: Main Features
- [ ] Chat interface
- [ ] Knowledge search
- [ ] Medical reports

### Phase 4: Additional Features
- [ ] Documents management
- [ ] Profile & Settings
- [ ] Admin dashboard

### Phase 5: Polish
- [ ] Animations
- [ ] Loading states
- [ ] Error handling
- [ ] Mobile optimization
- [ ] Accessibility audit

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Design Source**: Stitch Export (Nexus Intelligence)

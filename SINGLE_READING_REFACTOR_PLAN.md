# Plan: Refactor to Single Reading + Multiple Conversations Architecture

## Current System Analysis
- **Database**: User → Multiple Analyses → One Conversation per Analysis → Multiple Messages
- **UI**: Analyses page shows list of multiple readings, separate conversation page
- **Flow**: Users can create unlimited readings, each with one conversation thread

## Desired System
- **Database**: User → One Analysis (replaceable) → Multiple Conversations → Multiple Messages
- **UI**: Single reading page with persistent floating conversation input + dedicated conversation pages
- **Flow**: Users have one current reading with persistent conversation CTA, optimized for mobile-first engagement

## Required Changes

### 1. Database Schema Changes
- **Analyses table**: Add soft delete approach with `is_current` boolean instead of hard constraint
  ```sql
  ALTER TABLE analyses ADD COLUMN is_current BOOLEAN DEFAULT TRUE;
  CREATE UNIQUE INDEX idx_user_current_analysis ON analyses(user_id) WHERE is_current = TRUE;
  ```
- **Conversations table**:
  - Remove one-to-one constraint, allow multiple conversations per analysis
  - Add `topic` or `title` field for conversation organization
  - Add `created_at` for topic ordering
- **Migration strategy**: For existing users with multiple analyses, mark most recent as current, others as inactive
- **Cascading deletes**: When analysis changes, delete all associated conversations and files

### 2. Backend API Changes
- **Analysis creation**: Mark existing analysis as inactive before creating new one
- **Conversation endpoints**:
  - Allow multiple conversations per analysis
  - Add topic/title management endpoints
  - Version API endpoints for backward compatibility
- **User dashboard**: Update to show single current reading instead of multiple
- **Data cleanup**: Add service methods for analysis replacement and file cleanup logic
- **File management**: Implement scheduled cleanup for inactive analysis files

### 3. Frontend UI Changes (Mobile-First Revenue-Optimized Design)
- **Remove Dashboard**: Eliminate analyses list entirely - single reading is the primary interface
- **Main Reading Page** (`/reading` or `/analysis/{id}`):
  - Full scrollable reading content
  - **Persistent floating input bar** at bottom: "Ask about your reading..."
  - Bar remains fixed during scroll for constant conversation access
  - Auto-generate conversation titles from first message using OpenAI
- **Conversation Pages** (`/conversation/{id}`):
  - Clean chat interface with existing message design
  - Breadcrumb: "← Back to Reading" for easy navigation
  - Floating input for follow-up questions
- **Reading Management**:
  - "Redo Reading" button with enhanced warning modal
  - Show conversation count preview: "This will delete your 3 conversations"
  - Explicit confirmation checkbox required
- **Navigation Flow**:
  - Primary: Reading page (with floating CTA)
  - Secondary: Individual conversation pages
  - Reading page serves as home base for all interactions

### 4. File System Changes
- **Image storage**: Update cleanup logic for analysis replacement
- **OpenAI files**: Ensure proper deletion of old analysis assets
- **Cleanup timing**:
  - Immediate: Mark files for deletion when analysis is replaced
  - Scheduled: Daily cleanup job for inactive analysis files older than 7 days
  - Emergency cleanup: Manual cleanup commands for storage management

## Implementation Approach
1. **Database migration** with soft delete approach and conversation title fields
2. **Backend services** update with:
   - Single reading APIs (mark previous as inactive)
   - Multiple conversations per analysis support
   - Auto-title generation using OpenAI for conversations
   - Enhanced file cleanup with cascading deletes to OpenAI
3. **Frontend refactor** to mobile-first conversation-optimized design:
   - Remove dashboard entirely
   - Implement persistent floating conversation input
   - Create dedicated conversation pages with breadcrumb navigation
   - Enhanced "redo reading" warnings with conversation count preview
4. **Testing** focused on conversation engagement flow and mobile UX
5. **Deployment** all-at-once for all users (no gradual rollout needed)

## Risk Mitigation
- **Data backup** before migration with restoration procedures
- **Enhanced UX warnings** to prevent accidental conversation loss when redoing readings
- **Rollback strategy** with documented procedures if issues arise
- **Mobile UX testing** to ensure floating input works across devices
- **Conversation engagement monitoring** to validate revenue optimization success

## Business Impact
- **Revenue Focus**: Persistent floating input maximizes conversation engagement
- **Mobile Optimization**: Bottom floating bar follows native mobile UX patterns
- **User Journey**: Streamlined Reading → Question → Conversation → Back to Reading flow
- **Monetization**: Easy access to conversation input drives per-message revenue
### User Flow

This document defines the user journey based on `_docs/project-overview.md` and the clarified decisions below. It focuses on how the listed features connect from a user's perspective.

### Purpose (from overview)

- **Goal**: Help users understand their future through Indian palmistry.
- **How**: User uploads a hand image; the server uses OpenAI `gpt-4.1-mini` to analyze it; the user can ask follow-up questions; responses are returned via API and shown in the front-end.

### Core Segments and Transitions

1) **Entry**
   - User opens the web app.

2) **Authentication**
   - User can log in and log out via server-side authentication APIs.
   - Login is not required to upload images or trigger analysis.
   - After analysis, full results and conversation require login (a brief summary is visible prior to login).

3) **Start a New Reading**
   - Upload up to two images (one per hand: left and right) → Analyse → Get Results.
   - Analysis uses the OpenAI model as described in the overview.
   - Post-analysis, show a brief summary; prompt user to log in to view the full report and proceed to conversation.

4) **Conversation on the Analysis**
   - Available only after login.
   - Conversations are bound to a specific analysis (conversations are accessed through analyses).
   - User asks follow-up questions about the analysis results; server responds via the AI model; messages are shown in the UI.
   - Re-opening and continuing a conversation appends messages and persists the updated conversation in the database.

5) **Analyses Management**
   - List past analyses.
   - Select an analysis to view details and access its conversations.
   - Analyses list is separate from conversations (conversations are not accessed independently).

6) **Conversation Management**
   - Start a new conversation (from an analysis).
   - Fetch old conversations (from an analysis).
   - Update a conversation: rename title, edit metadata, continue chat (append messages), and where permitted, edit messages.
   - Delete a conversation (see deletion rules below).

7) **Logout**
   - User logs out via the Logout API.

### High-level User Journeys

- **New Reading**
  - Entry → Start a New Reading (Upload up to 2 images → Analyse → Summary) → Login/Register → Full Results → Conversation → (Start another conversation or end) → Logout.

- **Returning User**
  - Entry → Login → View Analyses List → Select Analysis → View Full Results → Open Conversation (continue or start new) → Update/Delete as needed → Logout.

### UI Surfaces (to guide architecture and UI work)

- Authentication surface: Login and visible Logout control.
- New Reading surface: Image upload (up to two images: left/right), analysis progression, summary and full results display.
- Analyses list surface: Paginated, most-recent-first list of analyses.
- Analysis detail surface: Full results; access to conversations for that analysis.
- Conversation surface: Threaded messages tied to the selected analysis.
- Conversation detail surface: View, continue, update, or delete a conversation.

### System Interactions (from overview)

- Server provides FastAPI endpoints for authentication, image upload (supporting up to two images per reading), analysis, results retrieval, analyses listing, and conversation operations (start/fetch/update/delete/talk) scoped to an analysis.
- Server uses the OpenAI `gpt-4.1-mini` model to analyze images and answer follow-up questions.
- Server persists user credentials, images, analyses, and conversations in a database.
- Deletion: Removing a conversation deletes all its associated data; removing an analysis cascades to delete its images and conversations.
- Fetch old conversations: Most recent first, page size 5 (scoped within the selected analysis).

### Decisions from Clarifications

- Upload and analysis allowed without login; after analysis, show a brief summary and require login to access full results and conversation.
- Each reading can include up to two images (left and right hands).
- Update conversation: rename, edit metadata, continue chat (append messages), and persist updated conversation to the database.
- Deletion is cascading: deleting a conversation removes all its data; deleting an analysis removes its images and all related conversations.
- Fetching old conversations: most recent first, page size 5.
- Analyses are surfaced separately; conversations are accessible only through analyses.

### Proposed Image Constraints (to be confirmed)

- File types: JPEG, PNG.
- Max file size: 15 MB per image.
- Recommended minimum resolution: 1024×1024.
- Require two distinct images when both hands are provided (one left, one right); allow single-hand reading with one image.

# Changelog

All notable changes to this project will be documented in this file.

## [v0.0.3] - 2025-12-07

### Added
- **Mobile Responsiveness**: Optimized UI for mobile devices with a responsive sidebar overlay and backdrop.
- **UX Improvements**: Added immediate typing indicator for better perceived latency.
- **Session Management**: Implemented explicit session creation and persistence to fix split sessions on refresh.

### Fixed
- **Chat Persistence**: Resolved issue where refreshing the page created a new chat session.
- **Sidebar Updates**: Fixed sidebar session list to update immediately upon creating a new chat.
- **Frontend Build**: Fixed build errors related to undefined variables.

### Changed
- **Backend**: Refactored `ChatService` and `ChatRouter` to handle session IDs explicitly via headers.

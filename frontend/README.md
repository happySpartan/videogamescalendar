# Video Game Calendar Frontend

## Overview

The Video Game Calendar frontend is a React application built with Vite, TypeScript, and Mantine UI. It provides a user-friendly interface for browsing upcoming video game releases, filtering by various criteria, and exporting release dates to calendar applications.

## Project Structure

### Core Folders

- `/src`: Main source code folder
  - `/components`: UI components used throughout the application
  - `/hooks`: Custom React hooks for reusable logic
  - `/services`: API service modules and data fetching logic
  - `/types`: TypeScript interfaces and type definitions
  - `/utils`: Helper functions and utility modules
  - `/styles`: Global CSS and styling utilities
  - `/theme`: Mantine theme configuration and customization

### Key Files

- `src/main.tsx`: Application entry point
- `src/App.tsx`: Root component that sets up the application
- `src/vite-env.d.ts`: Type definitions for Vite and environment variables
- `.env`: Environment variables configuration

## Component Structure

### Layout Components

- `Layout.tsx`: Main application layout with sidebar navigation
- `Header.tsx`: Top navigation bar with period selection and export options
- `SearchBar.tsx`: Global search interface for finding games

### Main Features

- `GameGrid.tsx`: Primary component for displaying game cards in a grid
- `FilterBar.tsx`: Filtering interface for platforms, genres, and languages
- `Calendar.tsx`: Calendar view component for visualizing releases by date
- `GameCard.tsx`: Individual game card display component

### Utility Components

- `ViewTitle.tsx`: Page title component with navigation options
- `AdminPanel.tsx`: Admin interface for managing backend data (if authorized)

## State Management

The application uses React's built-in state management with hooks like:

- `useState` for component-level state
- `useEffect` for side effects and API calls
- `useCallback` and `useMemo` for performance optimization

## Data Flow

1. User selects a view or time period (current month, week, etc.)
2. `GameGrid` component fetches data using `game.service.ts`
3. Games are displayed as cards with filtering and search options
4. Infinite scrolling loads more data when available

## API Communication

- `services/game.service.ts` handles all API requests to the backend
- Built-in caching reduces redundant API calls
- Environment variables in `.env` configure API endpoints

## Getting Started

### Prerequisites

- Node.js 16+ (18+ recommended)
- npm or yarn package manager
- Backend server running (see backend README)

### Installation

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install
# or
yarn
```

### Configuration

Create a `.env` file in the frontend directory:


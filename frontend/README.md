# Video Game Calendar Frontend

React application for browsing upcoming video game releases with modern UI.

## Features

- **Game Grid**: Browse games with infinite scrolling
- **Advanced Filtering**: Platforms, genres, languages, release periods
- **Search**: Real-time game search
- **Calendar View**: Visualize releases by date
- **Admin Panel**: System management (with admin access)

## Tech Stack

- React 18 with TypeScript
- Vite build tool
- Mantine UI components
- Custom hooks for API integration

## Setup

```bash
cd frontend
npm install
# Environment config lives in .env.development (gitignored) — it already contains
# sensible dev defaults (VITE_GAME_API_URL=http://localhost:8000). Override as needed.
npm run dev
```

## Project Structure

```
src/
├── api/          # Typed API client (client.ts, types.ts)
├── components/   # UI components
├── hooks/        # Custom React hooks (useReleaseCalendar, queries, ...)
├── pages/        # Route-level pages
├── styles/       # CSS / styling
├── theme/        # Mantine theme config
├── types/        # TypeScript definitions
└── utils/        # Helper functions
```

## Configuration

Environment variables in `.env.development`:


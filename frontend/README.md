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

# Copy environment file
cp .env.example .env.development
# Edit with your API endpoints

npm run dev
```

## Project Structure

```
src/
├── components/    # UI components
├── hooks/        # Custom React hooks
├── services/     # API service layer
├── types/        # TypeScript definitions
├── utils/        # Helper functions
└── theme/        # Mantine theme config
```

## Configuration

Environment variables in `.env.development`:


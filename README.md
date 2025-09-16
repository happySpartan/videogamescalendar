# Game Releases Calendar

This project is a web application that displays a calendar of future video game releases. It consists of a Flask backend and a React frontend, utilizing Mantine for UI components.

## Project Structure

```
game-releases-calendar
├── backend
│   ├── app.py                # Main entry point for the Flask application
│   ├── config.py             # Configuration settings for the Flask app
│   ├── requirements.txt       # Python dependencies for the backend
│   └── .env                  # Environment variables for the Flask app
├── frontend
│   ├── src
│   │   ├── components
│   │   │   ├── Calendar.tsx   # React component for the calendar interface
│   │   │   └── GameCard.tsx   # React component for displaying game information
│   │   ├── App.tsx            # Main React component for the application
│   │   ├── main.tsx           # Entry point for the React application
│   │   └── types
│   │       └── index.ts       # TypeScript interfaces and types
│   ├── package.json           # npm configuration file for the frontend
│   ├── tsconfig.json          # TypeScript configuration file
│   └── vite.config.ts         # Vite configuration for the frontend
├── .gitignore                 # Files and directories to ignore by Git
└── README.md                  # Documentation for the project
```

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd game-releases-calendar
   ```
2. **Backend Setup:**

   - Navigate to the `backend` directory.
   - Install the required Python packages:
     ```bash
     pip install -r requirements.txt
     ```
   - Set up your environment variables in the `.env` file.
   - Run the Flask application:
     
     **Standard mode (no SSL):**
     ```bash
     python run.py
     ```
     
     **With SSL support (for ZScaler environments):**
     
     On Windows (PowerShell):
     ```powershell
     # Run with default settings
     .\run_backend.ps1
     
     # To run without SSL
     .\run_backend.ps1 -NoSSL
     ```
     
     On Linux/Mac:
     ```bash
     chmod +x run_backend_ssl.sh
     ./run_backend_ssl.sh
     ```
     
     For more information on SSL configuration, see `backend/SSL_README.md`.
3. **Frontend Setup:**

   - Navigate to the `frontend` directory.
   - Install the required npm packages:
     ```bash
     npm install
     ```
   - Start the development server:
     ```bash
     npm run dev
     ```

## Usage

- Access the application in your web browser at `http://localhost:3000` (or the port specified by Vite).
- The calendar will display future video game releases fetched from the backend API.

## Contributing

Feel free to submit issues or pull requests to improve the project!

# Docker Setup

## Prerequisites

- Docker and Docker Compose installed on your system
- Twitch Developer account for IGDB API credentials
- ZScaler Root.pem certificate in your Downloads folder (for SSL support)

## Quick Start

1. Create a `.env` file in the project root directory with your credentials:

```
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
ADMIN_KEY=your_admin_key
```

2. Start the application using Docker Compose:

```bash
docker-compose up -d
```

This will start both the backend (with SSL support) and frontend services.

3. Access the application:
   - Frontend: http://localhost:80
   - Backend API: https://localhost:5050

## SSL Support in Docker

The Docker setup includes SSL support for ZScaler environments:

- The backend container is configured to use the Root.pem certificate from your Downloads folder
- The certificate is mounted as a volume in the container
- If the certificate is not found, the container will fall back to using default certificates

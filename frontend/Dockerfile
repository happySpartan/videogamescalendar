# Build stage
FROM node:18-alpine as build

# The public API URL the browser talks to. Baked in at build time (Vite reads it
# via process.env). Override when building the image so the deployed frontend
# calls the real API, e.g. --build-arg VITE_GAME_API_URL=https://api.calendar.example.com
ARG VITE_GAME_API_URL=http://localhost:8000
ENV VITE_GAME_API_URL=$VITE_GAME_API_URL

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy all files
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

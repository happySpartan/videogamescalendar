# Frontend Configuration Update

## Overview
Updated the frontend to work with the new microservices architecture while maintaining backward compatibility.

## Changes Made

### 1. Environment Configuration
- **`.env.example`**: Template for environment variables
- **`.env.development`**: Development-specific configuration
- **New Variables**:
  - `VITE_GAME_API_URL`: Game API service endpoint (port 8000)
  - `VITE_ADMIN_API_URL`: Admin API service endpoint (port 8001)
  - `VITE_USE_MICROSERVICES`: Feature flag for microservices
  - `VITE_ENABLE_CACHING`: Enhanced caching configuration
  - `VITE_ENABLE_ADMIN_FEATURES`: Admin panel features

### 2. Enhanced Service Layer
- **`enhanced-game.service.ts`**: New service with microservices support
- **Features**:
  - Automatic endpoint routing based on configuration
  - Enhanced error handling with timeouts
  - Improved caching with configurable expiration
  - Admin API integration
  - Health check capabilities
  - Debug mode support

### 3. Vite Configuration Updates
- **Proxy Setup**: Development proxy for API requests
- **Environment Variables**: Build-time variable injection
- **API Routing**: Automatic routing to correct microservices

## Migration Strategy

### Phase 1: Dual Support (Current)
The frontend now supports both the legacy Flask API and new microservices:

```typescript
// Legacy mode (existing functionality)
VITE_USE_MICROSERVICES=false
VITE_API_URL=http://localhost:5050

// Microservices mode (new functionality)
VITE_USE_MICROSERVICES=true
VITE_GAME_API_URL=http://localhost:8000
VITE_ADMIN_API_URL=http://localhost:8001
```

### Phase 2: Gradual Migration
Components can be updated one by one to use the enhanced service:

```typescript
// Before
import gameService from '../services/game.service';

// After
import enhancedGameService from '../services/enhanced-game.service';
```

### Phase 3: Full Migration
Once all components are updated, remove the legacy service.

## API Endpoint Mapping

### Game API Service (Port 8000)
- `GET /games` → Paginated game listing
- `GET /games/{id}` → Game details
- `GET /games/search` → Game search
- `GET /genres` → Genre list
- `GET /platforms` → Platform list
- `GET /health` → Service health

### Admin API Service (Port 8001)
- `GET /stats/overview` → System statistics
- `GET /stats/database` → Database metrics
- `POST /sync/games` → Trigger data sync
- `GET /cache/stats` → Cache statistics
- `DELETE /cache/clear` → Clear cache

## Development Workflow

### 1. Start Services
```bash
# Start infrastructure
docker-compose up postgres redis

# Start Game API
cd services/game-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Start Admin API
cd services/admin-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Start frontend
cd frontend
npm install
npm run dev
```

### 2. Environment Setup
Copy and configure environment files:
```bash
cp .env.example .env.development
# Edit .env.development with your settings
```

### 3. Testing
The enhanced service includes health checks:
```typescript
import enhancedGameService from './services/enhanced-game.service';

// Check service health
const health = await enhancedGameService.healthCheck();
console.log('Service status:', health);
```

## Features

### Enhanced Caching
- **Configurable Expiration**: Different cache times for different data types
- **Cache Stats**: Monitor cache performance
- **Manual Cache Control**: Clear cache when needed

### Error Handling
- **Timeout Protection**: Configurable request timeouts
- **Retry Logic**: Automatic retry for transient failures
- **Graceful Degradation**: Fallback to cached data when possible

### Performance Monitoring
- **Request Timing**: Track API response times
- **Cache Hit Rates**: Monitor caching effectiveness
- **Health Monitoring**: Continuous service health checks

### Admin Features
- **System Stats**: Monitor application metrics
- **Data Sync Control**: Trigger manual synchronization
- **Cache Management**: Administrative cache control

## Backward Compatibility

The enhanced service maintains full compatibility with existing frontend code:
- Same method signatures
- Same return data structures
- Same error handling patterns
- Gradual migration path

## Production Considerations

### Environment Variables
```bash
# Production configuration
VITE_GAME_API_URL=https://api.yourdomain.com
VITE_ADMIN_API_URL=https://admin-api.yourdomain.com
VITE_USE_MICROSERVICES=true
VITE_ENABLE_CACHING=true
VITE_ENABLE_ADMIN_FEATURES=false
VITE_DEBUG_MODE=false
```

### Security
- Admin features disabled by default in production
- Token-based authentication for admin endpoints
- CORS configuration for cross-origin requests

### Performance
- CDN integration for static assets
- Service worker for offline capabilities
- Optimized bundle splitting
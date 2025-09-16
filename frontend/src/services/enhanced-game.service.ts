"""
Frontend API Service Configuration
Updated service layer to work with the new microservices architecture
"""
import { Game, FilterOption, PaginatedResponse } from '../types';
import { GameResponse, GameFilterOptions } from '../types/game.types';

// Environment configuration
interface ApiConfig {
  gameApiUrl: string;
  adminApiUrl: string;
  useMicroservices: boolean;
  enableCaching: boolean;
  cacheExpiration: number;
  apiTimeout: number;
  pageSize: number;
  debugMode: boolean;
}

// Get configuration from environment variables
const getApiConfig = (): ApiConfig => ({
  gameApiUrl: import.meta.env.VITE_GAME_API_URL || 'http://localhost:8000',
  adminApiUrl: import.meta.env.VITE_ADMIN_API_URL || 'http://localhost:8001',
  useMicroservices: import.meta.env.VITE_USE_MICROSERVICES === 'true',
  enableCaching: import.meta.env.VITE_ENABLE_CACHING !== 'false',
  cacheExpiration: parseInt(import.meta.env.VITE_CACHE_EXPIRATION || '300000'), // 5 minutes
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '10000'), // 10 seconds
  pageSize: parseInt(import.meta.env.VITE_PAGE_SIZE || '20'),
  debugMode: import.meta.env.VITE_DEBUG_MODE === 'true'
});

// Simple in-memory cache
interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiresIn: number;
}

class EnhancedGameService {
  private config: ApiConfig;
  private cache: Map<string, CacheItem<any>> = new Map();
  
  constructor() {
    this.config = getApiConfig();
    
    if (this.config.debugMode) {
      console.log('Enhanced Game Service initialized with config:', this.config);
    }
  }
  
  // Helper method for making requests with timeout and error handling
  private async fetchWithTimeout<T>(
    url: string, 
    options: RequestInit = {}, 
    timeout: number = this.config.apiTimeout
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json() as T;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }
  
  // Get from cache or fetch
  private async getCachedOrFetch<T>(
    cacheKey: string,
    fetchFunction: () => Promise<T>,
    customExpiration?: number
  ): Promise<T> {
    const now = Date.now();
    
    // Check cache if caching is enabled
    if (this.config.enableCaching && this.cache.has(cacheKey)) {
      const cachedItem = this.cache.get(cacheKey)!;
      if (now - cachedItem.timestamp < cachedItem.expiresIn) {
        if (this.config.debugMode) {
          console.log(`Cache hit for ${cacheKey}`);
        }
        return cachedItem.data as T;
      } else {
        this.cache.delete(cacheKey);
      }
    }
    
    // Fetch fresh data
    if (this.config.debugMode) {
      console.log(`Cache miss for ${cacheKey}, fetching...`);
    }
    
    const data = await fetchFunction();
    
    // Store in cache
    if (this.config.enableCaching) {
      this.cache.set(cacheKey, {
        data,
        timestamp: now,
        expiresIn: customExpiration || this.config.cacheExpiration
      });
    }
    
    return data;
  }
  
  // Get paginated games with filtering
  public async getGames(options: GameFilterOptions = {}): Promise<PaginatedResponse<Game>> {
    const {
      page = 1,
      limit = this.config.pageSize,
      search,
      genre_id,
      platform_id,
      release_year
    } = options;
    
    // Build query parameters
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    if (search) params.append('search', search);
    if (genre_id) params.append('genre_id', genre_id.toString());
    if (platform_id) params.append('platform_id', platform_id.toString());
    if (release_year) params.append('release_year', release_year.toString());
    
    const endpoint = `/games?${params.toString()}`;
    const cacheKey = `games:${endpoint}`;
    
    return this.getCachedOrFetch(
      cacheKey,
      () => this.fetchWithTimeout<PaginatedResponse<Game>>(
        `${this.config.gameApiUrl}${endpoint}`
      ),
      300000 // 5 minutes for game lists
    );
  }
  
  // Get single game by ID
  public async getGameById(id: number): Promise<Game> {
    const endpoint = `/games/${id}`;
    const cacheKey = `game:${id}`;
    
    return this.getCachedOrFetch(
      cacheKey,
      () => this.fetchWithTimeout<Game>(
        `${this.config.gameApiUrl}${endpoint}`
      ),
      600000 // 10 minutes for individual games
    );
  }
  
  // Search games
  public async searchGames(query: string, limit: number = 10): Promise<{
    query: string;
    results: Game[];
    count: number;
  }> {
    const params = new URLSearchParams();
    params.append('q', query);
    params.append('limit', limit.toString());
    
    const endpoint = `/games/search?${params.toString()}`;
    const cacheKey = `search:${query}:${limit}`;
    
    return this.getCachedOrFetch(
      cacheKey,
      () => this.fetchWithTimeout(
        `${this.config.gameApiUrl}${endpoint}`
      ),
      600000 // 10 minutes for search results
    );
  }
  
  // Get genres
  public async getGenres(): Promise<FilterOption[]> {
    const cacheKey = 'genres:all';
    
    const genres = await this.getCachedOrFetch(
      cacheKey,
      () => this.fetchWithTimeout<any[]>(
        `${this.config.gameApiUrl}/genres`
      ),
      1800000 // 30 minutes for reference data
    );
    
    // Transform to FilterOption format
    return genres.map(genre => ({
      value: genre.id.toString(),
      label: genre.name
    }));
  }
  
  // Get platforms
  public async getPlatforms(): Promise<FilterOption[]> {
    const cacheKey = 'platforms:all';
    
    const platforms = await this.getCachedOrFetch(
      cacheKey,
      () => this.fetchWithTimeout<any[]>(
        `${this.config.gameApiUrl}/platforms`
      ),
      1800000 // 30 minutes for reference data
    );
    
    // Transform to FilterOption format
    return platforms.map(platform => ({
      value: platform.id.toString(),
      label: platform.name
    }));
  }
  
  // Admin API methods (if admin features are enabled)
  public async getSystemStats(): Promise<any> {
    if (!import.meta.env.VITE_ENABLE_ADMIN_FEATURES) {
      throw new Error('Admin features are not enabled');
    }
    
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      throw new Error('Admin authentication required');
    }
    
    return this.fetchWithTimeout(
      `${this.config.adminApiUrl}/stats/overview`,
      {
        headers: {
          'Authorization': `Bearer ${adminToken}`
        }
      }
    );
  }
  
  public async triggerGameSync(fullSync: boolean = false): Promise<any> {
    if (!import.meta.env.VITE_ENABLE_ADMIN_FEATURES) {
      throw new Error('Admin features are not enabled');
    }
    
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      throw new Error('Admin authentication required');
    }
    
    return this.fetchWithTimeout(
      `${this.config.adminApiUrl}/sync/games`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify(fullSync)
      }
    );
  }
  
  // Clear cache
  public clearCache(): void {
    this.cache.clear();
    if (this.config.debugMode) {
      console.log('Cache cleared');
    }
  }
  
  // Get cache stats
  public getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }
  
  // Health check
  public async healthCheck(): Promise<{
    gameApi: boolean;
    adminApi: boolean;
    errors: string[];
  }> {
    const errors: string[] = [];
    let gameApi = false;
    let adminApi = false;
    
    try {
      await this.fetchWithTimeout(`${this.config.gameApiUrl}/health`, {}, 5000);
      gameApi = true;
    } catch (error) {
      errors.push(`Game API: ${error.message}`);
    }
    
    try {
      await this.fetchWithTimeout(`${this.config.adminApiUrl}/health`, {}, 5000);
      adminApi = true;
    } catch (error) {
      errors.push(`Admin API: ${error.message}`);
    }
    
    return { gameApi, adminApi, errors };
  }
}

// Create singleton instance
const enhancedGameService = new EnhancedGameService();

export default enhancedGameService;
export { EnhancedGameService };
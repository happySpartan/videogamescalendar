import { Game, FilterOption, PaginatedResponse } from '../types';
import { GameResponse, GameFilterOptions } from '../types/game.types';

// Simple in-memory cache
interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiresIn: number; // milliseconds
}

class GameService {
  private baseUrl: string;
  private cache: Map<string, CacheItem<any>> = new Map();
  private cacheExpiration: number = 5 * 60 * 1000; // 5 minutes default
  private pageSize: number = 20; // Number of games per page
  
  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl || (import.meta.env.VITE_API_URL || 'http://localhost:5050');
  }
  
  // Helper method for making GET requests with caching
  public async get<T>(endpoint: string, useCache: boolean = true, cacheExpiration?: number): Promise<T> {
    const cacheKey = endpoint;
    const now = Date.now();
    
    // Try to get from cache if caching is enabled
    if (useCache && this.cache.has(cacheKey)) {
      const cachedItem = this.cache.get(cacheKey)!;
      if (now - cachedItem.timestamp < cachedItem.expiresIn) {
        console.log(`Using cached data for ${endpoint}`);
        return cachedItem.data as T;
      } else {
        // Cache expired, remove it
        this.cache.delete(cacheKey);
      }
    }
    
    // Not in cache or cache disabled, make the request
    try {
      console.log(`Fetching data from ${endpoint}`);
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json() as T;
      
      // Store in cache if caching is enabled
      if (useCache) {
        this.cache.set(cacheKey, {
          data,
          timestamp: now,
          expiresIn: cacheExpiration || this.cacheExpiration
        });
      }
      
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }
  
  // Get games based on view/period
  async getGamesByView(view: string): Promise<Game[]> {
    let endpoint = '';
    
    switch (view) {
      case 'This Month':
        endpoint = '/api/games?period=current_month';
        break;
      case 'Upcoming Releases':
        endpoint = '/api/games?period=upcoming';
        break;
      case 'This Year':
        endpoint = '/api/games?period=year';
        break;
      case 'Next Year': 
        endpoint = '/api/games?period=next_year';
        break;
     
        // Current week by default
        const now = new Date();
        const { start, end } = this.getWeekBounds(now);
        endpoint = `/api/games?period=date_range&start_date=${start.toISOString().split('T')[0]}&end_date=${end.toISOString().split('T')[0]}`;
        break;
      default:
        endpoint = '/api/games?period=current_month';
    }

    const response = await this.get<GameResponse>(endpoint);
    return response.games || [];
  }
    // Get games for a specific period (month or week)
  async getGamesByPeriod(period: { type: 'month' | 'week', date: Date }, page: number = 1): Promise<Game[]> {
    const offset = (page - 1) * this.pageSize;
    const limit = this.pageSize;
    
    let endpoint = '/api/games';
    const params = new URLSearchParams();
    
    if (period.type === 'month') {
      params.set('period', 'specific_month');
      params.set('year', period.date.getFullYear().toString());
      params.set('month', (period.date.getMonth() + 1).toString()); // JavaScript months are 0-based
    } else {
      const { start, end } = this.getWeekBounds(period.date);
      params.set('period', 'date_range');
      params.set('start_date', start.toISOString().split('T')[0]);
      params.set('end_date', end.toISOString().split('T')[0]);
    }
    
    params.set('page', page.toString());
    params.set('limit', limit.toString());
    
    endpoint += `?${params.toString()}`;
    console.log('Requesting games with endpoint:', endpoint);
    
    const response = await this.get<{games: Game[]; pagination: any}>(endpoint, true);
    return response.games || [];
  }
  
  // Helper to get week bounds
  private getWeekBounds(date: Date): { start: Date; end: Date } {
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1); // Adjust for Sunday
    
    const weekStart = new Date(date);
    weekStart.setDate(diff);
    weekStart.setHours(0, 0, 0, 0);
    
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    weekEnd.setHours(23, 59, 59, 999);
    
    return { start: weekStart, end: weekEnd };
  }
  
  // Get filter data (genres, platforms, languages)
  async getFilterOptions(): Promise<GameFilterOptions> {
    try {
      // Use longer cache expiration for reference data (1 hour)
      const hourInMs = 60 * 60 * 1000;
      const [platforms, genres, languages] = await Promise.all([
        this.getPlatforms(true, hourInMs),
        this.getGenres(true, hourInMs),
        this.getLanguages(true, hourInMs)
      ]);
      
      return {
        platforms,
        genres,
        languages
      };
    } catch (error) {
      console.error('Error fetching filter options:', error);
      return {
        platforms: [],
        genres: [],
        languages: []
      };
    }
  }
  
  // Get game genres
  async getGenres(useCache: boolean = true, cacheExpiration?: number): Promise<FilterOption[]> {
    return this.get<FilterOption[]>('/api/genres', useCache, cacheExpiration);
  }
  
  // Get game languages
  async getLanguages(useCache: boolean = true, cacheExpiration?: number): Promise<FilterOption[]> {
    return this.get<FilterOption[]>('/api/languages', useCache, cacheExpiration);
  }
  
  // Get game platforms
  async getPlatforms(useCache: boolean = true, cacheExpiration?: number): Promise<FilterOption[]> {
    return this.get<FilterOption[]>('/api/platforms', useCache, cacheExpiration);
  }
  
  // Get game companies/developers
  async getCompanies(useCache: boolean = true, cacheExpiration?: number): Promise<FilterOption[]> {
    return this.get<FilterOption[]>('/api/companies', useCache, cacheExpiration);
  }
  
  // Get game franchises
  async getFranchises(useCache: boolean = true, cacheExpiration?: number): Promise<FilterOption[]> {
    return this.get<FilterOption[]>('/api/franchises', useCache, cacheExpiration);
  }
  
  // Get specific game by ID
  async getGameById(id: number): Promise<Game> {
    return this.get<Game>(`/api/game/${id}`);
  }
  
  // Search for games
  async searchGames(query: string): Promise<Game[]> {
    if (!query || query.length < 2) {
      return [];
    }
    // Don't cache search results
    return this.get<Game[]>(`/api/games/search?q=${encodeURIComponent(query)}`, false);
  }
}

// Create and export singleton instance
export const gameService = new GameService();
export default gameService;

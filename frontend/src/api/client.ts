// Thin, typed fetch client for the game-api microservice.
// The single source of truth for how the frontend talks to the backend.
import type {
  GenreRef,
  PlatformRef,
  Release,
  ReleaseQueryParams,
  ReleasesResponse,
} from './types';

const BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_GAME_API_URL ||
  'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  private buildQuery(params: Record<string, string | number | undefined>): string {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        search.set(key, String(value));
      }
    }
    const qs = search.toString();
    return qs ? `?${qs}` : '';
  }

  private async getJSON<T>(path: string): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, { signal: controller.signal });
    } catch (error) {
      throw new ApiError(0, error instanceof Error ? error.message : 'Network error');
    } finally {
      clearTimeout(timeout);
    }

    if (!response.ok) {
      throw new ApiError(response.status, `API ${response.status}: ${response.statusText}`);
    }
    return (await response.json()) as T;
  }

  getReleases(params: ReleaseQueryParams = {}): Promise<ReleasesResponse> {
    return this.getJSON<ReleasesResponse>(
      `/releases${this.buildQuery({
        from: params.from,
        to: params.to,
        genre_id: params.genre_id,
        platform_id: params.platform_id,
        status: params.status,
        page: params.page,
        limit: params.limit,
      })}`,
    );
  }

  getRelease(id: number | string): Promise<Release> {
    return this.getJSON<Release>(`/games/${id}`);
  }

  getGenres(): Promise<GenreRef[]> {
    return this.getJSON<GenreRef[]>('/genres');
  }

  getPlatforms(): Promise<PlatformRef[]> {
    return this.getJSON<PlatformRef[]>('/platforms');
  }
}

export const apiClient = new ApiClient(BASE_URL);
export default apiClient;

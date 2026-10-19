// Thin, typed fetch client for the backend API, or the static JSON export.
// The single source of truth for how the frontend talks to the backend.
import type {
  GameDetail,
  GenreRef,
  PlatformRef,
  Release,
  ReleaseQueryParams,
  ReleasesResponse,
} from './types';

// Primary URL is VITE_GAME_API_URL (the documented, compose-wired build arg).
// VITE_API_URL is kept as a backward-compat alias for older setups.
const BASE_URL =
  import.meta.env.VITE_GAME_API_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000';

// Static mode (ADR-0004): read pre-built JSON from <base>/data instead of the API.
export const STATIC_DATA = import.meta.env.VITE_DATA_MODE === 'static';

/** Absolute URL of a calendar feed written by the static export (Phase 2). */
export function calendarFeedUrl(platformId?: number): string {
  const file = platformId ? `calendars/platform-${platformId}.ics` : 'calendar.ics';
  return new URL(`${import.meta.env.BASE_URL}data/${file}`, window.location.origin).href;
}

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
    if (STATIC_DATA) return this.getStaticReleases(params);
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

  /** Every release matching ``params``, following pagination (``page`` is ignored). */
  async getAllReleases(params: ReleaseQueryParams = {}): Promise<Release[]> {
    const first = await this.getReleases({ ...params, page: 1 });
    const rest = await Promise.all(
      Array.from({ length: Math.max(first.pagination.pages - 1, 0) }, (_, i) =>
        this.getReleases({ ...params, page: i + 2 }),
      ),
    );
    return [first, ...rest].flatMap((r) => r.releases);
  }

  getRelease(id: number | string): Promise<GameDetail> {
    return this.getJSON<GameDetail>(STATIC_DATA ? `/games/${id}.json` : `/games/${id}`);
  }

  // Arrow functions: the query hooks pass these as bare references.
  getGenres = (): Promise<GenreRef[]> =>
    this.getJSON<GenreRef[]>(STATIC_DATA ? '/genres.json' : '/genres');

  getPlatforms = (): Promise<PlatformRef[]> =>
    this.getJSON<PlatformRef[]>(STATIC_DATA ? '/platforms.json' : '/platforms');

  // Static mode (ADR-0004): answer /releases from the per-month JSON files,
  // applying the same filters, ordering and pagination as the API.
  private async getStaticReleases(params: ReleaseQueryParams): Promise<ReleasesResponse> {
    const today = new Date().toISOString().slice(0, 10);
    const from = params.from ?? (params.status === 'upcoming' ? today : undefined);
    const months = monthsBetween(from ?? today, params.to ?? addMonths(from ?? today, 12));

    const files = await Promise.all(
      months.map((m) =>
        this.getJSON<{ releases: Release[] }>(`/releases/${m}.json`).catch((error) => {
          // Months outside the exported window simply have no file.
          if (error instanceof ApiError && error.status === 404) return { releases: [] };
          throw error;
        }),
      ),
    );

    const now = new Date().toISOString();
    const matches = files
      .flatMap((f) => f.releases)
      .filter((r) => {
        const day = r.release_date?.slice(0, 10);
        if (!day) return params.status === 'tba';
        if (params.status === 'tba') return false;
        if (params.status === 'released' && r.release_date! > now) return false;
        if (params.status === 'upcoming' && r.release_date! <= now) return false;
        if (params.from && day < params.from) return false;
        if (params.to && day > params.to) return false;
        if (params.genre_id && !r.genres.some((g) => g.id === params.genre_id)) return false;
        if (params.platform_id && !r.platforms.some((p) => p.id === params.platform_id)) {
          return false;
        }
        return true;
      });

    const page = params.page ?? 1;
    const limit = params.limit ?? 50;
    const total = matches.length;
    return {
      releases: matches.slice((page - 1) * limit, page * limit),
      pagination: { page, limit, total, pages: Math.ceil(total / limit) },
    };
  }
}

/** YYYY-MM keys for every month touched by the [from, to] day range. */
function monthsBetween(from: string, to: string): string[] {
  const months: string[] = [];
  let [year, month] = from.slice(0, 7).split('-').map(Number);
  const last = to.slice(0, 7);
  for (;;) {
    const key = `${year}-${String(month).padStart(2, '0')}`;
    if (key > last) break;
    months.push(key);
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
  return months;
}

function addMonths(day: string, n: number): string {
  const d = new Date(`${day}T00:00:00Z`);
  d.setUTCMonth(d.getUTCMonth() + n);
  return d.toISOString().slice(0, 10);
}

export const apiClient = new ApiClient(STATIC_DATA ? `${import.meta.env.BASE_URL}data` : BASE_URL);
export default apiClient;

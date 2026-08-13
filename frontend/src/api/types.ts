// TypeScript types matching the backend API contract (services/game-api).
// The calendar primarily consumes GET /releases.

export interface GenreRef {
  id: number;
  name: string;
  slug?: string;
}

export interface PlatformRef {
  id: number;
  name: string;
  abbreviation?: string;
}

export interface CompanyRef {
  id: number;
  name: string;
  description?: string;
}

export interface Release {
  id: number;
  name: string;
  slug?: string;
  /** ISO datetime string from the backend, or null for TBA. */
  release_date: string | null;
  cover_url: string | null;
  rating?: number;
  genres: GenreRef[];
  platforms: PlatformRef[];
}

export interface ReleasesResponse {
  releases: Release[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface ReleaseQueryParams {
  from?: string; // YYYY-MM-DD
  to?: string; // YYYY-MM-DD
  genre_id?: number;
  platform_id?: number;
  status?: 'released' | 'upcoming' | 'tba';
  page?: number;
  limit?: number;
}

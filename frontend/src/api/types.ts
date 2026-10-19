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
  /** IGDB hypes + follows; orders games within a day (most anticipated first). */
  popularity?: number;
  genres: GenreRef[];
  platforms: PlatformRef[];
}

export interface GameVideo {
  /** YouTube video id. */
  video_id: string;
  name?: string | null;
}

export interface GameWebsite {
  url: string;
  /** Store name ("Steam", "PlayStation Store", ...) or null for other sites. */
  store: string | null;
}

/** GET /games/{id} (or games/<id>.json in static mode). */
export interface GameDetail extends Release {
  summary?: string | null;
  storyline?: string | null;
  screenshots?: string[] | null;
  videos?: GameVideo[] | null;
  websites?: GameWebsite[] | null;
  companies?: CompanyRef[];
}

/** A search suggestion (static search.json or GET /games/search). */
export interface SearchHit {
  id: number;
  name: string;
  release_date: string | null;
  cover_url: string | null;
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

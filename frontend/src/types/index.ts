// This file exports TypeScript interfaces and types used throughout the frontend application.

export interface Game {
  id: number;
  name: string;
  release_date: string;
  first_release_date?: string | null;
  cover_url: string | null;
  summary?: string;
  video_id?: string;
  developer?: { id: number; name: string };
  franchise?: { id: number; name: string };
  genre?: { id: number; name: string };
  language?: { id: number; name: string };
  platforms?: { id: number; name: string; abbreviation?: string }[];
  genres?: { id: number; name: string }[];
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  };
}

export interface FilterOption {
  id: number;
  name: string;
}
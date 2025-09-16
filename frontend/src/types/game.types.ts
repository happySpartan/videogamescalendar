import { Game, FilterOption } from './index';

export interface GameGridProps {
  view: string;
  searchQuery?: string;
}

export interface GameFilterOptions {
  platforms: FilterOption[];
  genres: FilterOption[];
  languages: FilterOption[];
}

export interface GameFilters {
  platforms: number[];
  genres: number[];
  languages: number[];
}

export interface GameResponse {
  games: Game[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  };
}

export interface PeriodType {
  type: 'month' | 'week' | 'day';
  date: Date;
}

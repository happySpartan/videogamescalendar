// Transitional service adapter.
//
// The GameLibraryContext still drives grid/list/header state, and it calls the
// methods below. Instead of hitting dead /api/* endpoints, this now delegates to
// the typed TanStack Query client (src/api/client.ts) against the real backend.
// New UI should use the query hooks in src/hooks/queries.ts directly; this shim
// will disappear once the context is fully replaced by TanStack Query.
import apiClient from '../api/client';
import { Game, FilterOption } from '../types';

export interface GameFilters {
  platforms?: number[];
  genres?: number[];
  languages?: number[];
  search?: string;
}

export interface GameFilterOptions {
  platforms: FilterOption[];
  genres: FilterOption[];
  languages: FilterOption[];
}

const pad = (n: number) => String(n).padStart(2, '0');

function getMonthBounds(date: Date): { from: string; to: string } {
  const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  return {
    from: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-01`,
    to: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(lastDay)}`,
  };
}

function getWeekBounds(date: Date): { from: string; to: string } {
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  const start = new Date(date);
  start.setDate(diff);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return {
    from: `${start.getFullYear()}-${pad(start.getMonth() + 1)}-${pad(start.getDate())}`,
    to: `${end.getFullYear()}-${pad(end.getMonth() + 1)}-${pad(end.getDate())}`,
  };
}

class GameService {
  async getGamesByPeriod(
    period: { type: 'month' | 'week' | 'day'; date: Date },
    page: number = 1,
    filters?: GameFilters,
  ): Promise<Game[]> {
    let from: string;
    let to: string;
    if (period.type === 'month') {
      ({ from, to } = getMonthBounds(period.date));
    } else if (period.type === 'week') {
      ({ from, to } = getWeekBounds(period.date));
    } else {
      const d = pad(period.date.getDate());
      from = `${period.date.getFullYear()}-${pad(period.date.getMonth() + 1)}-${d}`;
      to = from;
    }

    const data = await apiClient.getReleases({
      from,
      to,
      page,
      limit: 60,
      genre_id: filters?.genres?.[0],
      platform_id: filters?.platforms?.[0],
    });

    return (data.releases ?? []).map((r) => ({
      id: r.id,
      name: r.name,
      release_date: r.release_date ?? '',
      first_release_date: r.release_date,
      cover_url: r.cover_url,
      platforms: r.platforms,
      genres: r.genres,
    }));
  }

  async getFilterOptions(): Promise<GameFilterOptions> {
    const [platforms, genres] = await Promise.all([this.getPlatforms(), this.getGenres()]);
    return { platforms, genres, languages: [] };
  }

  async getGenres(): Promise<FilterOption[]> {
    return apiClient.getGenres();
  }

  async getPlatforms(): Promise<FilterOption[]> {
    return apiClient.getPlatforms();
  }

  async getLanguages(): Promise<FilterOption[]> {
    return [];
  }
}

export const gameService = new GameService();
export default gameService;

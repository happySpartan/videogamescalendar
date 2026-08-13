// Single data-layer hook for the grid/list/header views.
//
// Replaces the old GameLibraryContext reducer + game.service shim with one
// TanStack Query–backed hook. All data flows through the typed client
// (src/api/client.ts) and the query hooks (src/hooks/queries.ts); there is no
// second client or hand-rolled cache. Each view owns its own instance via
// local state, which is what the route-based pages expect.
import { useCallback, useMemo, useState } from 'react';
import { useGenres, usePlatforms, useReleases } from './queries';
import type { Game, FilterOption } from '../types';
import type { Release } from '../api/types';

const pad = (n: number) => String(n).padStart(2, '0');

function getMonthBounds(date: Date): { from: string; to: string } {
  const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  return {
    from: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-01`,
    to: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(lastDay)}`,
  };
}

function getWeekBoundsStr(date: Date): { from: string; to: string } {
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

/** Map a backend Release into the Game shape the legacy views render. */
function toGame(r: Release): Game {
  return {
    id: r.id,
    name: r.name,
    release_date: r.release_date ?? '',
    first_release_date: r.release_date ?? null,
    cover_url: r.cover_url,
    platforms: r.platforms ?? [],
    genres: r.genres ?? [],
  };
}

export interface CalendarViewOptions {
  /** Initial period. Defaults to the current month. */
  initialPeriod?: { type: 'month' | 'week' | 'day'; date: Date };
  /** Page size for the underlying /releases request. */
  limit?: number;
}

/**
 * Backs the grid/list/header views. Returns the same-shaped state the old
 * GameLibraryContext exposed (games, filters, period, search, pagination) but
 * sourced entirely through TanStack Query.
 */
export function useReleaseCalendar(
  options: CalendarViewOptions = {},
) {
  const { initialPeriod, limit = 60 } = options;
  const [period, setPeriod] = useState<{ type: 'month' | 'week' | 'day'; date: Date }>(
    initialPeriod ?? { type: 'month', date: new Date() },
  );
  const [page, setPage] = useState(1);
  const [platformIds, setPlatformIds] = useState<number[]>([]);
  const [genreIds, setGenreIds] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Reference data for the filter bar (long-lived cache).
  const { data: genresData } = useGenres();
  const { data: platformsData } = usePlatforms();
  const genres: FilterOption[] = (genresData ?? []).filter(
    (g): g is FilterOption => typeof g.id === 'number' && typeof g.name === 'string',
  );
  const platforms: FilterOption[] = (platformsData ?? []).filter(
    (p): p is FilterOption => typeof p.id === 'number' && typeof p.name === 'string',
  );

  // Date window for the current period.
  const bounds = useMemo(() => {
    if (period.type === 'day') {
      const d = pad(period.date.getDate());
      const day = `${period.date.getFullYear()}-${pad(period.date.getMonth() + 1)}-${d}`;
      return { from: day, to: day };
    }
    if (period.type === 'week') return getWeekBoundsStr(period.date);
    return getMonthBounds(period.date);
  }, [period]);

  const { data, isPending, isError, error } = useReleases({
    from: bounds.from,
    to: bounds.to,
    genre_id: genreIds[0],
    platform_id: platformIds[0],
    page,
    limit,
  });

  const releases: Release[] = data?.releases ?? [];
  const total = data?.pagination?.total ?? 0;
  const hasMore = data ? page * limit < total : false;

  const games: Game[] = useMemo(() => releases.map(toGame), [releases]);

  // Client-side search + filter as a deterministic layer on top of the API
  // result (the API filters by a single genre/platform id; we additionally
  // narrow on the multi-list selections and the search text).
  const filteredGames = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return games.filter((g) => {
      if (q) {
        const nameHit = g.name.toLowerCase().includes(q);
        const sumHit = g.genres?.some((gen) => gen.name.toLowerCase().includes(q));
        if (!nameHit && !sumHit) return false;
      }
      if (platformIds.length > 0 && !g.platforms?.some((p) => platformIds.includes(p.id))) {
        return false;
      }
      if (genreIds.length > 0 && !g.genres?.some((gen) => genreIds.includes(gen.id))) {
        return false;
      }
      return true;
    });
  }, [games, searchQuery, platformIds, genreIds]);

  const changePeriod = useCallback(
    (next: { type: 'month' | 'week' | 'day'; date: Date }) => {
      setPeriod(next);
      setPage(1);
    },
    [],
  );

  const loadMore = useCallback(() => {
    setPage((p) => p + 1);
  }, []);

  const resetFilters = useCallback(() => {
    setPlatformIds([]);
    setGenreIds([]);
    setSearchQuery('');
    setPage(1);
  }, []);

  return {
    games,
    filteredGames,
    loading: isPending,
    isError,
    error: isError ? (error instanceof Error ? error.message : 'Failed to load games') : null,
    page,
    hasMore,
    periods: { type: period.type, date: period.date },
    filterOptions: { platforms, genres, languages: [] as FilterOption[] },
    filters: { platforms: platformIds, genres: genreIds, languages: [] as number[] },
    searchQuery,
    setSearchQuery,
    setPlatformFilter: setPlatformIds,
    setGenreFilter: setGenreIds,
    changePeriod,
    loadMore,
    resetFilters,
  };
}

export type ReleaseCalendar = ReturnType<typeof useReleaseCalendar>;

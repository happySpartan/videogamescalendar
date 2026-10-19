// Shared data layer for the header and the calendar/grid/list views.
//
// One ReleaseCalendarProvider (in Layout) owns the period, filters and search
// text, so the header's navigation, period toggle and search box drive the
// page below it. All data flows through the typed client (src/api/client.ts)
// and the query hooks (src/hooks/queries.ts).
import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { useAllReleases, useGenres, usePlatforms } from './queries';
import type { Game, FilterOption } from '../types';
import type { Release } from '../api/types';

export type PeriodType = 'month' | 'week';
export interface Period {
  type: PeriodType;
  date: Date;
}

const pad = (n: number) => String(n).padStart(2, '0');
const isoDay = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

/** Monday-first week containing ``date`` (EU convention). */
export function getWeekStart(date: Date): Date {
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
  return start;
}

/** Inclusive YYYY-MM-DD bounds of the period. */
export function getPeriodBounds(period: Period): { from: string; to: string } {
  if (period.type === 'week') {
    const start = getWeekStart(period.date);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    return { from: isoDay(start), to: isoDay(end) };
  }
  const { date } = period;
  return {
    from: isoDay(new Date(date.getFullYear(), date.getMonth(), 1)),
    to: isoDay(new Date(date.getFullYear(), date.getMonth() + 1, 0)),
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

function useReleaseCalendarState() {
  const [period, setPeriod] = useState<Period>({ type: 'month', date: new Date() });
  const [platformIds, setPlatformIds] = useState<number[]>([]);
  const [genreIds, setGenreIds] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Reference data for the filter bar (long-lived cache).
  const { data: genresData } = useGenres();
  const { data: platformsData } = usePlatforms();
  const genres: FilterOption[] = useMemo(
    () => (genresData ?? []).filter((g) => typeof g.id === 'number' && typeof g.name === 'string'),
    [genresData],
  );
  const platforms: FilterOption[] = useMemo(
    () => (platformsData ?? []).filter((p) => typeof p.id === 'number' && typeof p.name === 'string'),
    [platformsData],
  );

  // A period is at most a month, so load all of it (every page) and filter
  // client-side; no infinite scrolling that could drop or repeat games.
  const bounds = useMemo(() => getPeriodBounds(period), [period]);
  const { data, isPending, isError, error } = useAllReleases({ ...bounds, limit: 500 });

  const releases: Release[] = useMemo(() => data ?? [], [data]);
  const games: Game[] = useMemo(() => releases.map(toGame), [releases]);

  const filteredReleases = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return releases.filter((r) => {
      if (q && !r.name.toLowerCase().includes(q) && !r.genres.some((g) => g.name.toLowerCase().includes(q))) {
        return false;
      }
      if (platformIds.length > 0 && !r.platforms.some((p) => platformIds.includes(p.id))) return false;
      if (genreIds.length > 0 && !r.genres.some((g) => genreIds.includes(g.id))) return false;
      return true;
    });
  }, [releases, searchQuery, platformIds, genreIds]);
  const filteredGames: Game[] = useMemo(() => filteredReleases.map(toGame), [filteredReleases]);

  const changePeriod = useCallback((next: Period) => setPeriod(next), []);

  /** Move the period one month/week back (-1) or forward (+1). */
  const shiftPeriod = useCallback((delta: number) => {
    setPeriod((p) => {
      const date = new Date(p.date);
      if (p.type === 'month') {
        return { type: p.type, date: new Date(date.getFullYear(), date.getMonth() + delta, 1) };
      }
      date.setDate(date.getDate() + 7 * delta);
      return { type: p.type, date };
    });
  }, []);

  const resetFilters = useCallback(() => {
    setPlatformIds([]);
    setGenreIds([]);
    setSearchQuery('');
  }, []);

  return {
    games,
    filteredGames,
    filteredReleases,
    loading: isPending,
    isError,
    error: isError ? (error instanceof Error ? error.message : 'Failed to load games') : null,
    periods: period,
    filterOptions: { platforms, genres },
    filters: { platforms: platformIds, genres: genreIds },
    searchQuery,
    setSearchQuery,
    setPlatformFilter: setPlatformIds,
    setGenreFilter: setGenreIds,
    changePeriod,
    shiftPeriod,
    resetFilters,
  };
}

export type ReleaseCalendar = ReturnType<typeof useReleaseCalendarState>;

const ReleaseCalendarContext = createContext<ReleaseCalendar | null>(null);

export function ReleaseCalendarProvider({ children }: { children: React.ReactNode }) {
  const value = useReleaseCalendarState();
  return <ReleaseCalendarContext.Provider value={value}>{children}</ReleaseCalendarContext.Provider>;
}

/** The shared calendar state; must be used under ReleaseCalendarProvider. */
export function useReleaseCalendar(): ReleaseCalendar {
  const value = useContext(ReleaseCalendarContext);
  if (!value) throw new Error('useReleaseCalendar must be used within ReleaseCalendarProvider');
  return value;
}

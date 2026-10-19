// TanStack Query hooks for the release-calendar data layer.
// These replace the homegrown in-memory caching in the old service layer.
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { Release, ReleaseQueryParams, ReleasesResponse } from '../api/types';

const FIVE_MIN = 5 * 60 * 1000;
const THIRTY_MIN = 30 * 60 * 1000;

/** Releases in a date window (or "upcoming"/"tba"). Returns the paginated payload. */
export function useReleases(params: ReleaseQueryParams = {}) {
  return useQuery<ReleasesResponse>({
    queryKey: ['releases', params],
    queryFn: () => apiClient.getReleases(params),
    staleTime: FIVE_MIN,
    placeholderData: keepPreviousData,
  });
}

/** All releases in a window, every page combined (the month calendar shows them all). */
export function useAllReleases(params: Omit<ReleaseQueryParams, 'page'> = {}) {
  return useQuery<Release[]>({
    queryKey: ['releases', 'all', params],
    queryFn: () => apiClient.getAllReleases(params),
    staleTime: FIVE_MIN,
    placeholderData: keepPreviousData,
  });
}

/** Games releasing from now onward (the "upcoming" list). */
export function useUpcomingReleases(limit = 100) {
  return useReleases({ status: 'upcoming', limit });
}

/** Reference data — cached for a long time because it changes rarely. */
export function useGenres() {
  return useQuery({
    queryKey: ['genres'],
    queryFn: apiClient.getGenres,
    staleTime: THIRTY_MIN,
  });
}

export function usePlatforms() {
  return useQuery({
    queryKey: ['platforms'],
    queryFn: apiClient.getPlatforms,
    staleTime: THIRTY_MIN,
  });
}

export function useRelease(id: number | string) {
  return useQuery({
    queryKey: ['release', id],
    queryFn: () => apiClient.getRelease(id),
    staleTime: THIRTY_MIN,
  });
}

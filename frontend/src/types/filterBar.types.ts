/**
 * Type definitions for the FilterBar component
 */

import { FilterOption } from './index';

export interface FilterBarProps {
  /**
   * Available platforms for filtering
   */
  platforms: FilterOption[];
  
  /**
   * Available genres for filtering
   */
  genres?: FilterOption[];
  
  /**
   * Available languages for filtering
   */
  languages?: FilterOption[];
  
  /**
   * Callback for when platform filters change
   */
  onPlatformFilterChange: (selected: number[]) => void;
  
  /**
   * Callback for when genre filters change
   */
  onGenreFilterChange?: (selected: number[]) => void;
  
  /**
   * Callback for when language filters change
   */
  onLanguageFilterChange?: (selected: number[]) => void;
}

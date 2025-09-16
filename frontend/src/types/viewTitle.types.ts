/**
 * Type definitions for the ViewTitle component
 */

export interface ViewTitleProps {
  /**
   * Main title text
   */
  title: string;
  
  /**
   * Optional subtitle or description text
   */
  subtitle?: string;
  
  /**
   * Whether to show a back button
   * @default false
   */
  showBackButton?: boolean;
  
  /**
   * Function to call when back button is clicked
   */
  onBack?: () => void;
  
  /**
   * Whether to show filter toggle button
   * @default false
   */
  showFilters?: boolean;
  
  /**
   * Function to call when filter button is clicked
   */
  onToggleFilters?: () => void;
}

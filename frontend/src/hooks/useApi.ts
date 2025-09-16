import { useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5050';

const useApi = () => {
  const get = useCallback(async <T>(endpoint: string): Promise<T> => {
    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json() as T;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }, []);

  const post = useCallback(async <T>(endpoint: string, data: any): Promise<T> => {
    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json() as T;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }, []);

  // Expose API_URL as baseUrl for components that need it
  return { get, post, baseUrl: API_URL };
};

export default useApi;
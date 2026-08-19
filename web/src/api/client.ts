import axios from 'axios';

export const USERNAME_STORAGE_KEY = 'neurotype.username';

const API_BASE_URL = `${import.meta.env.VITE_API_URL ?? '/api/v1'}`;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Every request carries the remembered username; the backend treats it as the current user.
apiClient.interceptors.request.use((config) => {
  const username = localStorage.getItem(USERNAME_STORAGE_KEY);
  if (username) {
    config.headers.set('X-Username', username);
  }
  return config;
});

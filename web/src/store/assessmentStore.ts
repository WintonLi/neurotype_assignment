import { create } from 'zustand';
import { USERNAME_STORAGE_KEY } from '../api/client';

interface AssessmentStore {
  username: string | null;
  login: (username: string) => void;
  logout: () => void;
}

export const useAssessmentStore = create<AssessmentStore>((set) => ({
  username: localStorage.getItem(USERNAME_STORAGE_KEY),
  login: (username) => {
    localStorage.setItem(USERNAME_STORAGE_KEY, username);
    set({ username });
  },
  logout: () => {
    localStorage.removeItem(USERNAME_STORAGE_KEY);
    set({ username: null });
  },
}));

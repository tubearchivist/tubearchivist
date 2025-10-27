import { create } from 'zustand';

interface BackendState {
  startTimestamp: string | null;
  setStartTimestamp: (timestamp: string) => void;
}

export const useBackendStore = create<BackendState>((set, get) => ({
  startTimestamp: null,
  setStartTimestamp: timestamp => {
    const prev = get().startTimestamp;
    if (prev && prev !== timestamp) {
      console.warn('Backend restart detected — reloading frontend...');
      window.location.reload();
    }
    set({ startTimestamp: timestamp });
  },
}));

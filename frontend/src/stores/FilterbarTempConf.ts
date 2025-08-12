// temporary values for filtering, not stored in backend

import { create } from 'zustand';

interface FilterbarTempConfInterface {
  filterHeight: string;
  setFilterHeight: (filterHeight: string) => void;
}

export const useFilterBarTempConf = create<FilterbarTempConfInterface>(set => ({
  filterHeight: '',
  setFilterHeight: (filterHeight: string) => set({ filterHeight }),
}));

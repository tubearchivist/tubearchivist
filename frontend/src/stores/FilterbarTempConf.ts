// temporary values for filtering, not stored in backend

import { create } from 'zustand';

interface FilterbarTempConfInterface {
  filterHeight: string;
  setFilterHeight: (filterHeight: string) => void;
  showFilterItems: boolean;
  setShowFilterItems: (filterItems: boolean) => void;
}

export const useFilterBarTempConf = create<FilterbarTempConfInterface>(set => ({
  filterHeight: '',
  setFilterHeight: (filterHeight: string) => set({ filterHeight }),
  showFilterItems: false,
  setShowFilterItems: (showFilterItems: boolean) => set({ showFilterItems }),
}));

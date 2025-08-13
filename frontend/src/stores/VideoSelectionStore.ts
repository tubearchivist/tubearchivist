import { create } from 'zustand';

interface SelectionState {
  selectedVideoIds: string[];
  appendVideoId: (id: string) => void;
  removeVideoId: (id: string) => void;
  clearSelected: () => void;
  showSelection: boolean;
  setShowSelection: (showSelection: boolean) => void;
  selectedAction: ((ids: string[]) => void) | null;
  setSelectedAction: (fn: ((ids: string[]) => void) | null) => void;
}

export const useVideoSelectionStore = create<SelectionState>(set => ({
  selectedVideoIds: [],

  appendVideoId: id =>
    set(state => {
      if (state.selectedVideoIds.includes(id)) {
        return state; // avoid duplicates
      }
      return { selectedVideoIds: [...state.selectedVideoIds, id] };
    }),

  removeVideoId: id =>
    set(state => ({
      selectedVideoIds: state.selectedVideoIds.filter(item => item !== id),
    })),

  clearSelected: () => set({ selectedVideoIds: [] }),

  showSelection: false,
  setShowSelection: (showSelection: boolean) => set({ showSelection }),

  selectedAction: null,
  setSelectedAction: fn => set({ selectedAction: fn }),
}));

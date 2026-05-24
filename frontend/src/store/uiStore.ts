import { create } from 'zustand';

interface UIState {
  isSourcesPanelOpen: boolean;
  isEvaluationPanelOpen: boolean;
  isSidebarOpen: boolean;
  selectedSourceIndex: number | null;
  highlightedCitation: number | null;

  toggleSourcesPanel: () => void;
  toggleEvaluationPanel: () => void;
  toggleSidebar: () => void;
  selectSource: (index: number | null) => void;
  highlightCitation: (index: number | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSourcesPanelOpen: true,
  isEvaluationPanelOpen: true,
  isSidebarOpen: true,
  selectedSourceIndex: null,
  highlightedCitation: null,

  toggleSourcesPanel: () => set((state) => ({ isSourcesPanelOpen: !state.isSourcesPanelOpen })),
  toggleEvaluationPanel: () => set((state) => ({ isEvaluationPanelOpen: !state.isEvaluationPanelOpen })),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  selectSource: (index: number | null) => set({ selectedSourceIndex: index }),
  highlightCitation: (index: number | null) => set({ highlightedCitation: index }),
}));

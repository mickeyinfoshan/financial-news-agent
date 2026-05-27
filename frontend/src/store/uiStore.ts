import { create } from 'zustand';

interface UIState {
  isSourcesPanelOpen: boolean;
  isEvaluationPanelOpen: boolean;
  isSidebarOpen: boolean;
  selectedSourceId: number | null;
  highlightedCitation: number | null;
  selectedMessageId: string | null;

  toggleSourcesPanel: () => void;
  toggleEvaluationPanel: () => void;
  toggleSidebar: () => void;
  selectSource: (id: number | null) => void;
  highlightCitation: (index: number | null) => void;
  selectMessage: (messageId: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSourcesPanelOpen: true,
  isEvaluationPanelOpen: true,
  isSidebarOpen: true,
  selectedSourceId: null,
  highlightedCitation: null,
  selectedMessageId: null,

  toggleSourcesPanel: () => set((state) => ({ isSourcesPanelOpen: !state.isSourcesPanelOpen })),
  toggleEvaluationPanel: () => set((state) => ({ isEvaluationPanelOpen: !state.isEvaluationPanelOpen })),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  selectSource: (id: number | null) => set({ selectedSourceId: id }),
  highlightCitation: (index: number | null) => set({ highlightedCitation: index }),
  selectMessage: (messageId: string | null) => set({ selectedMessageId: messageId }),
}));

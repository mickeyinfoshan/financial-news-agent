# Financial News Agent - Frontend

React + Vite + Zustand frontend for the Financial News Agent.

## Features

- 🔄 Real-time streaming responses with Server-Sent Events
- 📚 Citation linking to news sources
- 📊 Quality evaluation display with scores
- 💬 Multi-session conversation management
- 📱 Responsive design (desktop, tablet, mobile)
- 🎯 Interactive source highlighting

## Tech Stack

- **React 19** - UI framework
- **Vite 8** - Build tool
- **Zustand 5** - State management
- **Tailwind CSS 4** - Styling
- **TypeScript 6** - Type safety
- **Lucide React** - Icons
- **date-fns** - Date formatting

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Environment Variables

Create a `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Development

### Running Frontend + Backend Together

**Option 1: Two terminals**

```bash
# Terminal 1: Backend
cd ..
uv run python -m financial_news_agent.api_server

# Terminal 2: Frontend
npm run dev
```

**Option 2: Use the backend's CORS settings**

The backend is already configured to allow `http://localhost:5173` in CORS origins.

### Project Structure

```
src/
├── api/              # API client layer
│   ├── client.ts     # Base fetch wrapper
│   ├── sessions.ts   # Session endpoints
│   ├── queries.ts    # Query endpoints
│   └── streaming.ts  # SSE streaming
├── components/       # React components
│   ├── chat/         # Chat interface
│   ├── layout/       # Layout components
│   ├── session/      # Session management
│   └── sources/      # Sources panel
├── hooks/            # Custom React hooks
├── store/            # Zustand stores
├── types/            # TypeScript types
├── utils/            # Utility functions
├── App.tsx           # Root component
└── main.tsx          # Entry point
```

## Usage

1. **Create a session**: Click "New Session" in the sidebar
2. **Ask a question**: Type your query about stocks, companies, or industries
3. **View streaming response**: Watch the agent think, search, and write in real-time
4. **Explore sources**: Click citations `[1]`, `[2]` to see source articles
5. **Check quality**: View evaluation scores for each response
6. **Multi-turn conversation**: Continue asking follow-up questions

## Key Features

### Citation System

Citations in the agent's response are clickable links that:
- Highlight the corresponding source in the sources panel
- Scroll to the source automatically
- Show tooltips with source titles on hover

### Streaming

Real-time streaming shows:
- Thinking indicator
- Tool calls (e.g., "Searching NewsAPI...")
- Token-by-token response generation
- Evaluation progress

### Quality Scores

Each response includes evaluation scores (1-10):
- **Overall**: Average quality score
- **Accuracy**: Information matches sources
- **Relevance**: Addresses the query
- **Coherence**: Logical storyline
- **Reasonableness**: Plausible future impact

Color coding:
- 🟢 8-10: Excellent
- 🟡 6-7.9: Good
- 🟠 4-5.9: Needs improvement
- 🔴 0-3.9: Poor

### Retry History

When the agent automatically retries to improve quality, you'll see:
- Number of retry attempts
- Previous answers and scores
- Final improved response

## Building for Production

```bash
# Build
npm run build

# Preview production build
npm run preview
```

Output will be in `dist/` directory.

## Troubleshooting

### CORS Errors

Make sure the backend's `.env` includes:
```bash
API_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### API Connection Failed

1. Check backend is running: `curl http://localhost:8000/api/v1/health`
2. Verify `VITE_API_BASE_URL` in `.env`
3. Check browser console for errors

### Streaming Not Working

1. Ensure backend supports SSE (it does by default)
2. Check network tab for `/query/stream` endpoint
3. Verify no proxy/firewall blocking SSE

## License

Part of the Financial News Agent project.

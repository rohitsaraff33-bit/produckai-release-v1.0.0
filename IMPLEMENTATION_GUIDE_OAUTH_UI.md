# ProduckAI: OAuth + Cursor UI Implementation Guide

## Overview

This guide covers implementing two major upgrades:

- **Part A**: OAuth + Token Refresh (Google & Zoom) - IMPLEMENTED BELOW
- **Part B**: Cursor-style Dark UI - BLUEPRINT PROVIDED

---

## Part A: OAuth + Token Refresh ✅

### Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │─────▶│  FastAPI     │─────▶│  Provider   │
│             │◀─────│  /auth/*     │◀─────│  (G/Zoom)   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  oauth_tokens│
                     │  (encrypted) │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Celery Beat  │
                     │ (auto-refresh│
                     └──────────────┘
```

### Files Created

#### 1. Core Services

- `apps/api/core/secrets.py` - AES-GCM encryption
- `apps/api/auth/providers/base.py` - Base OAuth provider
- `apps/api/auth/providers/google_oauth.py` - Google OAuth with PKCE
- `apps/api/auth/providers/zoom_oauth.py` - Zoom OAuth with PKCE

#### 2. Database

- `apps/api/models/oauth.py` - OAuthToken model
- `infra/alembic/versions/003_add_oauth_tokens.py` - Migration

#### 3. API

- `apps/api/api/auth.py` - Auth endpoints router

#### 4. Workers

- `apps/worker/tasks/token_refresh.py` - Celery beat task

---

## Part B: Cursor-Style UI Blueprint 📐

### Design System

**Color Tokens** (add to `globals.css`):

```css
:root {
  /* Dark editor theme */
  --bg: #0b0e14;
  --panel: #0f131a;
  --panel-2: #11161d;
  --border: #1b2230;
  --muted: #7f8da3;
  --text: #d7e0f2;
  --accent: #4c8bff;
  --accent-2: #65d6ad;
  --warning: #e6b450;

  /* Semantic */
  --sidebar-width: 48px;
  --explorer-min: 220px;
  --copilot-min: 320px;
}
```

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ [Icon Nav]  [Explorer]        [Main Editor]      [Copilot] │
│   48px      220-400px           Flex              320-500px │
│                                                               │
│  🏠 Home   ┌──────────┐   ┌───────────────────┐  ┌────────┐│
│  📊 Themes │ Top      │   │ Tab1 │ Tab2 │ Tab3│  │/insights│
│  🔍 Search │  Themes  │   ├───────────────────┤  ├────────┤│
│  🔗 Integ  │  ▸ Auth  │   │                   │  │Results │
│  ⚙️ Settings│  ▸ Billing│   │   Theme Cards    │  │with    │
│            │          │   │   Grid           │  │citations│
│            │ Sources  │   │                   │  │        │
│            │  ▸ Slack │   │                   │  └────────┘│
│            │  ▸ Zoom  │   └───────────────────┘             │
│            └──────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
AppShell
├── SidebarIconNav (48px fixed)
├── ResizablePanelGroup (horizontal)
│   ├── ExplorerPanel (220-400px, collapsible)
│   │   ├── SectionHeader
│   │   ├── ThemeTree (virtualized)
│   │   └── SourceFilters
│   ├── MainEditor (flex)
│   │   ├── TabBar (closeable tabs)
│   │   ├── ThemesBoard (tab content)
│   │   ├── ThemeDetail (tab content)
│   │   └── PRDDraft (tab content with Monaco)
│   └── CopilotPanel (320-500px, togglable)
│       ├── CommandInput (slash autocomplete)
│       ├── ResultsRenderer
│       └── CitationList
└── CommandPalette (⌘K overlay)
```

### Package.json Additions

```json
{
  "dependencies": {
    "react-resizable-panels": "^2.0.0",
    "cmdk": "^1.0.0",
    "@monaco-editor/react": "^4.6.0",
    "lucide-react": "^0.300.0",
    "framer-motion": "^11.0.0"
  }
}
```

### Key Components to Build

#### 1. AppShell.tsx

```tsx
"use client";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "react-resizable-panels";
import SidebarIconNav from "./SidebarIconNav";
import ExplorerPanel from "./ExplorerPanel";
import CopilotPanel from "./CopilotPanel";

export default function AppShell({ children }) {
  return (
    <div className="h-screen flex bg-[--bg] text-[--text]">
      <SidebarIconNav />
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel defaultSize={20} minSize={15} maxSize={30}>
          <ExplorerPanel />
        </ResizablePanel>
        <ResizableHandle />
        <ResizablePanel>{children}</ResizablePanel>
        <ResizableHandle />
        <ResizablePanel defaultSize={25} minSize={20} maxSize={35}>
          <CopilotPanel />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
```

#### 2. CommandPalette.tsx

```tsx
"use client";
import { Command } from "cmdk";
import { useEffect, useState } from "react";

export default function CommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  return (
    <Command.Dialog open={open} onOpenChange={setOpen}>
      <Command.Input placeholder="Type a command or search..." />
      <Command.List>
        <Command.Group heading="Actions">
          <Command.Item
            onSelect={() => {
              /* ingest demo */
            }}
          >
            Ingest Demo Data
          </Command.Item>
          <Command.Item
            onSelect={() => {
              /* run clustering */
            }}
          >
            Run Clustering
          </Command.Item>
          <Command.Item
            onSelect={() => {
              /* open integrations */
            }}
          >
            Open Integrations
          </Command.Item>
        </Command.Group>
        <Command.Group heading="Themes">
          {/* Fuzzy search themes */}
        </Command.Group>
      </Command.List>
    </Command.Dialog>
  );
}
```

#### 3. CopilotPanel.tsx

```tsx
"use client";
import { useState } from "react";

export default function CopilotPanel() {
  const [input, setInput] = useState("");
  const [results, setResults] = useState([]);

  const runCommand = async () => {
    const res = await fetch("/api/copilot/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cmd: input }),
    });
    const data = await res.json();
    setResults([...results, data]);
  };

  return (
    <div className="h-full flex flex-col bg-[--panel] border-l border-[--border]">
      <div className="p-4 border-b border-[--border]">
        <h2 className="font-semibold">Copilot</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {results.map((r, i) => (
          <div key={i} className="bg-[--panel-2] p-3 rounded">
            <pre className="text-sm">{JSON.stringify(r, null, 2)}</pre>
          </div>
        ))}
      </div>
      <div className="p-4 border-t border-[--border]">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runCommand()}
          placeholder="/insights, /justify, /draft-prd"
          className="w-full bg-[--bg] border border-[--border] rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[--accent]"
        />
      </div>
    </div>
  );
}
```

### Implementation Steps (UI)

1. **Install dependencies**

   ```bash
   cd apps/web
   npm install react-resizable-panels cmdk @monaco-editor/react lucide-react framer-motion
   ```

2. **Update globals.css** with dark theme tokens

3. **Create component structure**

   ```
   components/
   ├── layout/
   │   ├── AppShell.tsx
   │   ├── SidebarIconNav.tsx
   │   ├── ExplorerPanel.tsx
   │   ├── CopilotPanel.tsx
   │   └── TabBar.tsx
   ├── CommandPalette.tsx
   ├── ThemeCard.tsx (update for dark)
   └── CitationChip.tsx (update with icons)
   ```

4. **Update root layout** to use AppShell

5. **Add keyboard shortcuts** (⌘K, ⌘., ⌘B, ⌘1/2/3)

6. **Create settings pages**
   - `/settings/integrations` - OAuth connections UI

7. **Add UI helper endpoints**
   - `GET /ui/entities` - for explorer tree
   - `POST /copilot/run` - command execution

### Testing Checklist

- [ ] ⌘K opens command palette
- [ ] ⌘. toggles Copilot panel
- [ ] ⌘B toggles Explorer
- [ ] Panels resize smoothly
- [ ] Dark theme contrast meets WCAG AA
- [ ] Keyboard navigation works throughout
- [ ] OAuth connect/disconnect flows work
- [ ] Token auto-refresh happens silently
- [ ] Copilot commands execute and show citations

---

## Deployment Notes

### Environment Variables

```bash
# OAuth (required for live mode)
APP_SECRET=<base64-encoded-32-bytes>
OAUTH_REDIRECT_BASE_URL=http://localhost:8000

# Google
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# Zoom
ZOOM_CLIENT_ID=xxx
ZOOM_CLIENT_SECRET=xxx
```

### OAuth Redirect URIs

Configure in provider consoles:

- **Google**: `http://localhost:8000/auth/google/callback`
- **Zoom**: `http://localhost:8000/auth/zoom/callback`

### Celery Beat

Update `docker-compose.yml` to add beat service:

```yaml
beat:
  build: ./apps/worker
  command: celery -A apps.worker.celery_app beat --loglevel=info
  depends_on:
    - redis
  env_file:
    - .env
```

---

## Timeline Estimate

- **OAuth Backend**: 4-6 hours (implemented below)
- **UI Layout + Components**: 12-16 hours
- **Command Palette + Shortcuts**: 4-6 hours
- **Integrations Page**: 3-4 hours
- **Monaco Editor + PRD Draft**: 4-6 hours
- **Testing + Polish**: 6-8 hours

**Total**: ~35-50 hours of development

---

## Next Steps

1. Review OAuth implementation below
2. Test OAuth flows with Google/Zoom
3. Begin UI implementation using blueprints above
4. Iterate on design system
5. Add telemetry and monitoring

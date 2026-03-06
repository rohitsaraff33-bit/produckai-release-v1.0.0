# ⚡ Quick Start: OAuth + Cursor UI

## 📦 What's Been Created

```
✅ CREATED - Ready to use:
apps/api/core/secrets.py
apps/api/auth/__init__.py
apps/api/auth/providers/__init__.py
apps/api/auth/providers/base.py
apps/api/auth/providers/google_oauth.py
apps/api/auth/providers/zoom_oauth.py
apps/api/models/oauth.py

📖 DOCS - Copy code from:
OAUTH_CURSOR_UI_IMPLEMENTATION.md        # Complete OAuth code
IMPLEMENTATION_GUIDE_OAUTH_UI.md         # UI blueprints + design system
UPGRADE_SUMMARY_OAUTH_CURSOR_UI.md       # Full status & checklist
```

---

## 🚀 5-Minute Setup

### 1. Generate APP_SECRET

```bash
python -c 'import os,base64; print("APP_SECRET=" + base64.b64encode(os.urandom(32)).decode())'
# Copy output to .env
```

### 2. Create Missing Files

**Migration** (`infra/alembic/versions/003_add_oauth_tokens.py`):

```bash
# Open OAUTH_CURSOR_UI_IMPLEMENTATION.md
# Search for "003_add_oauth_tokens"
# Copy code to new file
```

**Auth Endpoints** (`apps/api/api/auth.py`):

```bash
# Open OAUTH_CURSOR_UI_IMPLEMENTATION.md
# Search for "apps/api/api/auth.py"
# Copy code to new file
```

**Celery Task** (`apps/worker/tasks/token_refresh.py`):

```bash
# Open OAUTH_CURSOR_UI_IMPLEMENTATION.md
# Search for "token_refresh.py"
# Copy code to new file
```

### 3. Update Existing Files

**`apps/api/main.py`** - Add auth router:

```python
from apps/api.api.auth import router as auth_router
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
```

**`docker-compose.yml`** - Add beat service:

```yaml
beat:
  build: ./apps/worker
  command: celery -A apps.worker.celery_app beat --loglevel=info
  depends_on:
    - redis
    - postgres
  env_file:
    - .env
```

**`.env`** - Add OAuth config:

```bash
APP_SECRET=<generated-above>
OAUTH_REDIRECT_BASE_URL=http://localhost:8000
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ZOOM_CLIENT_ID=
ZOOM_CLIENT_SECRET=
```

### 4. Deploy & Test

```bash
# Rebuild
docker compose down
TMPDIR=/tmp docker compose build api worker
TMPDIR=/tmp docker compose up -d

# Migrate
docker compose exec api alembic upgrade head

# Test OAuth start
curl http://localhost:8000/auth/google/start
# Open returned URL in browser

# Check connection
curl http://localhost:8000/auth/connections
```

---

## 📋 File Tree

```
ProduckAI/
│
├── apps/api/
│   ├── core/
│   │   └── secrets.py                           ✅ Created
│   ├── auth/
│   │   ├── __init__.py                          ✅ Created
│   │   └── providers/
│   │       ├── __init__.py                      ✅ Created
│   │       ├── base.py                          ✅ Created
│   │       ├── google_oauth.py                  ✅ Created
│   │       └── zoom_oauth.py                    ✅ Created
│   ├── models/
│   │   └── oauth.py                             ✅ Created
│   ├── api/
│   │   ├── main.py                              📝 Update (add auth router)
│   │   └── auth.py                              📝 Create (copy from docs)
│   └── services/
│       ├── google_client.py                     📝 Update (token store integration)
│       └── zoom_client.py                       📝 Update (token store integration)
│
├── apps/worker/
│   ├── celery_app.py                            📝 Update (beat schedule)
│   └── tasks/
│       └── token_refresh.py                     📝 Create (copy from docs)
│
├── infra/alembic/versions/
│   └── 003_add_oauth_tokens.py                  📝 Create (copy from docs)
│
├── apps/web/  (Cursor UI - Phase 2)
│   ├── package.json                             📝 Update (add dependencies)
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css                      📝 Update (dark theme)
│   │   │   ├── layout.tsx                       📝 Update (AppShell)
│   │   │   └── settings/integrations/
│   │   │       └── page.tsx                     📝 Create (OAuth UI)
│   │   └── components/
│   │       ├── layout/
│   │       │   ├── AppShell.tsx                 📝 Create
│   │       │   ├── SidebarIconNav.tsx           📝 Create
│   │       │   ├── ExplorerPanel.tsx            📝 Create
│   │       │   └── CopilotPanel.tsx             📝 Create
│   │       └── CommandPalette.tsx               📝 Create
│
├── docker-compose.yml                            📝 Update (beat service)
├── .env                                          📝 Update (OAuth config)
│
└── 📖 DOCUMENTATION (all ✅ created):
    ├── IMPLEMENTATION_GUIDE_OAUTH_UI.md
    ├── OAUTH_CURSOR_UI_IMPLEMENTATION.md
    └── UPGRADE_SUMMARY_OAUTH_CURSOR_UI.md
```

---

## 🎯 Commands Summary

```bash
# === Phase 1: OAuth Backend (Today) ===

# 1. Generate secret
python -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())'

# 2. Create 3 files from docs:
# - infra/alembic/versions/003_add_oauth_tokens.py
# - apps/api/api/auth.py
# - apps/worker/tasks/token_refresh.py

# 3. Update 4 files:
# - apps/api/main.py (add auth router)
# - docker-compose.yml (add beat service)
# - apps/worker/celery_app.py (beat schedule)
# - .env (OAuth config)

# 4. Deploy
docker compose down
TMPDIR=/tmp docker compose build api worker
TMPDIR=/tmp docker compose up -d

# 5. Migrate
docker compose exec api alembic upgrade head

# 6. Test
curl http://localhost:8000/auth/google/start
curl http://localhost:8000/auth/connections
curl http://localhost:8000/docs  # See new /auth/* endpoints

# === Phase 2: Cursor UI (Next Week) ===

# 1. Install deps
cd apps/web && npm install react-resizable-panels cmdk @monaco-editor/react lucide-react framer-motion

# 2. Update globals.css with dark theme

# 3. Create components (see blueprints in docs)

# 4. Test
npm run dev
open http://localhost:3000
# Press ⌘K for command palette
# Press ⌘. for copilot panel
```

---

## 📚 Documentation Map

| File                                 | Purpose                 | What's Inside                               |
| ------------------------------------ | ----------------------- | ------------------------------------------- |
| `QUICK_START_OAUTH_UI.md`            | **This file**           | Quick commands & file tree                  |
| `UPGRADE_SUMMARY_OAUTH_CURSOR_UI.md` | Status dashboard        | What's done, what's left, testing checklist |
| `OAUTH_CURSOR_UI_IMPLEMENTATION.md`  | Complete code reference | All OAuth code + UI starters                |
| `IMPLEMENTATION_GUIDE_OAUTH_UI.md`   | Detailed guide          | UI blueprints, design system, architecture  |

---

## ⏱️ Time Estimates

| Task                                 | Time           | Status  |
| ------------------------------------ | -------------- | ------- |
| **OAuth Backend**                    |                |         |
| Copy 3 files from docs               | 15 min         | ⏳ TODO |
| Update 4 files                       | 15 min         | ⏳ TODO |
| Configure OAuth apps (Google + Zoom) | 30 min         | ⏳ TODO |
| Test OAuth flow                      | 20 min         | ⏳ TODO |
| **SUBTOTAL**                         | **1.5 hours**  |         |
|                                      |                |         |
| **Cursor UI**                        |                |         |
| Install dependencies                 | 5 min          | ⏳ TODO |
| Dark theme tokens                    | 20 min         | ⏳ TODO |
| AppShell + layout                    | 4 hours        | ⏳ TODO |
| Command Palette                      | 3 hours        | ⏳ TODO |
| Copilot Panel                        | 3 hours        | ⏳ TODO |
| Explorer Panel                       | 4 hours        | ⏳ TODO |
| Integrations page                    | 3 hours        | ⏳ TODO |
| Theme components (dark)              | 4 hours        | ⏳ TODO |
| Monaco editor integration            | 4 hours        | ⏳ TODO |
| Keyboard shortcuts                   | 2 hours        | ⏳ TODO |
| Testing + polish                     | 6 hours        | ⏳ TODO |
| **SUBTOTAL**                         | **33 hours**   |         |
|                                      |                |         |
| **GRAND TOTAL**                      | **34.5 hours** |         |

---

## ✅ Verification Checklist

### OAuth Backend (Phase 1)

- [ ] APP_SECRET generated and in `.env`
- [ ] Migration file created
- [ ] Auth endpoints file created
- [ ] Celery task file created
- [ ] Auth router added to main.py
- [ ] Beat service added to docker-compose.yml
- [ ] Google OAuth app configured
- [ ] Zoom OAuth app configured
- [ ] Migration runs successfully
- [ ] `/auth/google/start` returns authorization URL
- [ ] OAuth callback completes successfully
- [ ] Token stored in database (encrypted)
- [ ] `/auth/connections` returns active tokens
- [ ] Token can be decrypted correctly
- [ ] Disconnect revokes token
- [ ] Celery beat runs every 10 minutes

### Cursor UI (Phase 2)

- [ ] Dependencies installed
- [ ] Dark theme applied
- [ ] AppShell renders
- [ ] Panels resize smoothly
- [ ] ⌘K opens command palette
- [ ] ⌘. toggles copilot
- [ ] ⌘B toggles explorer
- [ ] Keyboard nav works
- [ ] Integrations page shows OAuth status
- [ ] Connect/disconnect works from UI
- [ ] Monaco editor loads PRD drafts
- [ ] Citation chips show source icons
- [ ] Lighthouse scores meet targets

---

## 🆘 Troubleshooting

**Issue**: Migration fails with "enum already exists"

```bash
# Reset database
docker compose down -v
docker compose up -d postgres
docker compose exec api alembic upgrade head
```

**Issue**: Cannot import oauth providers

```bash
# Check files exist
ls apps/api/auth/providers/
# Should show: __init__.py base.py google_oauth.py zoom_oauth.py
```

**Issue**: Token decryption fails

```bash
# Verify APP_SECRET is 32 bytes when base64-decoded
python -c 'import base64; print(len(base64.b64decode("YOUR_SECRET")))'
# Should output: 32
```

**Issue**: OAuth callback fails

```bash
# Check redirect URI matches exactly in OAuth app config
# Must be: http://localhost:8000/auth/google/callback
```

---

## 🎓 Learn More

- **OAuth 2.0 + PKCE**: https://oauth.net/2/pkce/
- **Google OAuth Setup**: https://console.cloud.google.com
- **Zoom OAuth Setup**: https://marketplace.zoom.us/develop/create
- **React Resizable Panels**: https://github.com/bvaughn/react-resizable-panels
- **cmdk (Command Palette)**: https://cmdk.paco.me
- **Monaco Editor**: https://microsoft.github.io/monaco-editor/

---

## 🎉 Success Indicators

✅ **OAuth Working**:

- Open `/auth/google/start` → redirects to Google
- Complete OAuth flow → see "Success" message
- Check `/auth/connections` → see active token
- Celery beat logs show "refresh_expiring_tokens" scheduled

✅ **UI Working**:

- Press ⌘K → command palette opens
- Press ⌘. → copilot panel toggles
- Themes render in dark mode
- Source chips show correct icons
- Panels resize smoothly

---

**Ready to start?** Follow the 5-Minute Setup above! 🚀

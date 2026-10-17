# Dr. Mojtahedi — Django API

Multi-app DRF backend for the foundation site and staff admin.

## Apps

| App | Domain |
|-----|--------|
| `accounts` | Member OTP, staff JWT, dashboard stats |
| `heritage` | People, places, timeline |
| `content` | News, magazine, library |
| `archive` | Archive items, oral history |
| `foundation` | Projects, sponsors, organs, collaborate |
| `engagement` | Newsletter, contributions, contact |
| `ai` | Chat config + rule-based chat |
| `common` | Base models, `seed_content` command |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_content
python manage.py runserver
```

Default staff user from seed: `admin` / `admin123456`

API base: `http://127.0.0.1:8000/api/v1/`

### Auth

- Staff: `POST /api/v1/auth/admin/login/` → JWT access/refresh
- Member OTP: `POST /api/v1/auth/otp/send/` + `/verify/` (demo code `123456` when `OTP_DEMO=true`)

### Notable routes

- Public: `/news/`, `/people/`, `/archive/`, `/sponsors/`, `/newsletter/`, `/contribute/`, `/ai/chat/`
- Admin (Bearer staff JWT): `/admin/news/`, `/admin/people/`, `/admin/archive/`, `/admin/sponsors/`, `/admin/newsletter/`, `/admin/contributions/`, `/admin/dashboard/`

Local DB is SQLite; swap `DATABASES` for MySQL in production.

# Deployment Guide

TournamentManager is deployed on [Render](https://render.com) using the Python buildpack, with a PostgreSQL database hosted on [Miget](https://miget.com).

---

## Architecture

- **Web service:** Render free tier (Python 3 buildpack)
- **Database:** Miget PostgreSQL free tier
- **Static files:** WhiteNoise (served directly by Django/Gunicorn)
- **Media files:** Azure Blob Storage (sponsor banners)
- **Authentication:** django-allauth with Google OAuth

---

## Environment Variables

Set these in the Render dashboard under **Environment**:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Set to `False` in production |
| `DATABASE_URL` | Full PostgreSQL connection string from Miget |
| `ALLOWED_HOSTS` | `tournamentmanager.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://tournamentmanager.onrender.com` |
| `AZURE_ACCOUNT_NAME` | Azure storage account name |
| `AZURE_ACCOUNT_KEY` | Azure storage account key |
| `AZURE_CONNECTION_STRING` | Azure connection string |
| `AZURE_CONTAINER` | Azure container name for media |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` (or SMTP in future) |

---

## Render Service Configuration

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| Start command | `python manage.py migrate && gunicorn myproject.wsgi:application --bind 0.0.0.0:10000` |
| Auto-deploy | Enabled on push to `main` |

---

## First Deploy — Required Manual Steps

### 1. Run migrations
Migrations run automatically on every deploy via the start command. No manual step needed.

### 2. Create the Site object (required for Google OAuth)

Django's `sites` framework creates a default `Site` with `id=1` and domain `example.com` during the initial migration. Allauth requires a `Site` matching the actual domain.

1. Go to `/admin/sites/site/`
2. Either edit the existing `example.com` entry or create a new one
3. Set domain to `tournamentmanager.onrender.com` and display name to `TournamentManager`
4. Note the `id` of this site
5. Set `SITE_ID` in `settings.py` to match — currently `SITE_ID = 2`

> If deploying fresh, the Site id may differ. Check the admin and update `SITE_ID` accordingly.

### 3. Configure Google OAuth

1. Go to `/admin/socialaccount/socialapp/`
2. Create a new Social Application:
   - Provider: Google
   - Name: Google
   - Client ID: from Google Cloud Console
   - Secret key: from Google Cloud Console
3. Move the correct Site from "Available sites" to "Chosen sites"

### 4. Create a superuser

```bash
python manage.py createsuperuser
```

---

## Local Development

### Without Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
SECRET_KEY=your-local-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

```bash
python manage.py migrate
python manage.py runserver
```

### With Docker

```bash
docker-compose up --build
```

Create a `.env` file in the project root:

```
SECRET_KEY=your-local-secret-key
DEBUG=True
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=tournament
DATABASE_URL=postgresql://postgres:postgres@db:5432/tournament
ALLOWED_HOSTS=localhost,127.0.0.1
```

App will be available at `http://localhost` (via nginx) or `http://localhost:8000` (directly).

---

## Running Tests

```bash
pytest tests/
```

With coverage:

```bash
pytest tests/ --cov=tournamentapp --cov-report=html
```

---

## Tournament Day Checklist

Free tier services are not suitable for live event traffic. Before the tournament:

- [ ] Upgrade Render instance to at least $7/month
- [ ] Verify Miget database is not sleeping
- [ ] Add `conn_health_checks=True` to database config
- [ ] Test the public spectator URL from a fresh incognito window
- [ ] Confirm sponsor banners are uploading correctly to Azure
- [ ] Downgrade Render back to free after the event

---

## Known Limitations

- **Free tier cold start:** Render free instances spin down after inactivity. First request after idle can take 50+ seconds. Upgrade before the tournament.
- **SITE_ID:** Must match a manually created Site object in the admin. If redeploying from scratch, verify this before testing OAuth.
- **Azure media in production only:** In local development, media files use the local filesystem. Azure Blob Storage is only active when `DEBUG=False`.
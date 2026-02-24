# Tournament Manager
A Django-based web application to manage sports tournaments, including teams, players, matches, scheduling, and leaderboards.

## Features
- Create and manage tournaments
- Add teams, players, and fields
- Generate round-robin match schedules automatically
- Track match results and events (goals, own goals, cards)
- Public and private tournament views
- Leaderboard calculation with tiebreakers
- CSV batch import for teams and players
- Admin and user access control

## Technology Stack
- Backend: Django 4.x, Python 3.12
- Database: SQLite / PostgreSQL (configurable)
- Frontend: Django templates, HTML/CSS
- Authentication: Custom user model with email login
- Testing: Pytest, Django test framework, coverage
- CI/CD: GitHub Actions pipeline

## GitHub Actions CI Pipeline
- Automatically installs dependencies
- Runs tests and generates coverage report
- Uploads htmlcov as an artifact
- Environment variables are set in the workflow

## License
MIT License see LICENSE for details.

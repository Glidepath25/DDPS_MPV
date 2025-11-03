# DDPS Workflow Portal

DDPS is a workflow management portal covering quotation, design, fabrication, and delivery stages for pipe support jobs. The initial product is a Django application with Bootstrap-powered server-rendered views so you can demo quickly while keeping the door open for a richer frontend later.

## Local setup

1. Create and activate the virtual environment (already configured as `.venv`):
   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Copy `.env` and adjust values as needed. Set a strong `SECRET_KEY` and configure `DATABASE_URL` when deploying.
4. Apply database migrations:
   ```powershell
   python manage.py migrate
   ```
5. (Optional) Seed demo data:
   ```powershell
   python manage.py seed_demo
   ```
   Demo logins:
   - Admin: `admin` / `Admin123!`
   - Sikla manager: `sikla.manager` / `Demo123!`
   - Client user (Harland Steel): `client.jane` / `Demo123!`
6. Run the development server:
   ```powershell
   python manage.py runserver
   ```

## Key features

- **Role-aware dashboards**: Sikla/internal team members see every project; client users only see their assigned client portfolio.
- **Project hierarchy**: Clients -> Projects -> Jobs with milestone tracking for Created, Requirements Analysis, Drawing Completion, Client Approval, Fabrication, Quality Control, and Delivery.
- **Excel exports**: Download job and milestone data as `.xlsx` directly from the UI.
- **Milestone management**: Edit planned and actual milestone dates inline on the job detail page.
- **Access controls**: User flags determine visibility for finance, programme, technical, and client information; finance numbers stay hidden for users without that flag.
- **Demo seeding**: `seed_demo` populates representative data for immediate walkthroughs.

## Deployment notes

- Set `DATABASE_URL` for Postgres (DigitalOcean Managed DB recommended). The app falls back to SQLite locally.
- Configure `ALLOWED_HOSTS`, `SECRET_KEY`, and any email settings through environment variables before production deploys.
- Run `python manage.py collectstatic` when serving static assets outside of Django.
- To extend automation (notifications, scheduled exports), plug Celery/Redis into the service layer in `projects/services.py`.

## Suggested next steps

1. Add automated tests for permissions and milestone workflows (Django test suite or pytest).
2. Introduce a REST or GraphQL API layer to support a React/Next.js experience later.
3. Build a lightweight user management screen for toggling finance/programme/technical/client detail flags.
4. Attach drawing files using DigitalOcean Spaces or another object store.
5. Add alerting (email or Teams/Slack) for milestone slippage or new client approvals.

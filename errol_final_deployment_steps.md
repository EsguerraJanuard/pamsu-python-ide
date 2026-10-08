# Final Backend Deployment Steps (For Errol)

Hey Errol! The frontend is fully completed on the `dev` branch for the final defense, including the new Enterprise Login and the Super Admin Dashboard. However, the live production environment is currently broken because the Render backend is out of sync with the Vercel frontend. 

Please execute the following steps to get production 100% ready for the panelists:

### 1. Merge `dev` into `main`
Render is currently deploying from the `main` branch, but all our recent backend updates were pushed to the `dev` branch. 
*   **Action:** Create a Pull Request and merge `dev` into `main`. This will trigger Render to build the latest backend (which includes the Admin endpoints, Guest auto-enrollment, and Name-splitting refactor).

### 2. Run Database Migrations (Critical)
The `dev` branch includes a new Alembic migration (`c5d2f62cc22e`) that splits the `name` column into `first_name`, `middle_name`, and `last_name`, and adds the `admin` role constraint.
*   **Action:** Ensure that `alembic upgrade head` runs on the Render production database so the new schema is applied. If your Render start command doesn't do this automatically, please run it manually.

### 3. Fix CORS for Vercel Preview URLs
Januard is currently getting a **"Cannot connect to the server (CORS issue)"** error because he is testing on a Vercel preview URL (`https://pamsu-python-mybigzo5w-esguerrajanuards-projects.vercel.app`). The backend currently only allows the main production URL.
*   **Action:** In the Render dashboard, update the `PAMSU_CORS_ALLOWED_ORIGINS` environment variable to include regex or wildcard support for Vercel preview URLs (e.g., allow `https://*.vercel.app`), or just explicitly tell Januard to ONLY test using the main URL: `https://pamsu-python-ide.vercel.app`.

### 4. Initialize the Super Admin Account
To prevent the DB constraint from failing when the MIS logs in, a temporary seed endpoint was added to the router.
*   **Action:** Once Render finishes deploying the updated `main` branch, manually visit `https://pamsu-backend.onrender.com/admin/seed-production` in your browser. It will securely inject the `admin@pampangastateu.edu.ph` account (Password: `Admin@2026`) into the production database.

Once those 4 steps are done, production will be flawless for the final defense. Let me know if you run into any DB constraint issues during the migration!

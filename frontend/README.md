# Front End

React + TypeScript app for Lore Lens, built with Vite.

## Prerequisites

- Node 20+ (matches the Docker image)

## Getting Started

Install dependencies:
```bash
npm install
```

Copy the example env file and adjust if your backend runs somewhere other than `http://localhost:8080`:
```bash
cp .env.example .env
```
`VITE_API_URL` controls the backend base URL used by `src/api/client.ts`. If unset, it falls back to `http://localhost:8080`.

Start the dev server:
```bash
npm run dev
```
The app is served at `http://localhost:5173` by default.

### Running via Docker

From the repo root:
```bash
docker compose up --build
```
This serves the frontend at `http://localhost:3000` and the backend at `http://localhost:8080`. See the root `README.md` for the full stack.

Note: the backend allows credentialed CORS requests from `http://localhost:5173` and `http://localhost:3000` by default (see `backend/.env.example`'s `CORS_ALLOWED_ORIGINS`). If you serve the frontend from a different origin, add it to that variable on the backend.

## Routes

- `/login` — sign-in page
- `/home` — temporary placeholder page shown after a successful login
- `/` — redirects to `/login`

## Testing

Tests use [Vitest](https://vitest.dev/) with [Testing Library](https://testing-library.com/) and run in a jsdom environment (configured in `vite.config.ts`, setup file at `src/test/setup.ts`).

Run the full suite once:
```bash
npm run test
```

Run in watch mode:
```bash
npm run test:watch
```

Run a single file:
```bash
npx vitest run src/pages/LoginPage/LoginPage.test.tsx
```

Tests are colocated with the code they cover (e.g. `LoginPage.tsx` / `LoginPage.test.tsx`).

## Type Checking

```bash
npx tsc -b
```

## Linting

```bash
npm run lint
```

## Production Build

```bash
npm run build
```
Runs a type check (`tsc -b`) followed by `vite build`. Output goes to `dist/`.

Preview the production build locally:
```bash
npm run preview
```

## Project Structure

```
src/
  api/          fetch-based API client and typed error mapping
  components/   reusable UI components (TextField, Button, FormError)
  pages/        route-level pages (LoginPage, HomePage)
  test/         Vitest setup (Testing Library cleanup, jest-dom matchers)
```

## Expanding the ESLint Configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

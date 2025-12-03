# Translation of Frontend Hexagonal Architecture Migration Tasks

Here's the translation to English for Claude Code:

---

## 2. Target Structure for `anvil_frontend/src`

Starting from your example and applying it to this project:

```text
src/
  setup/
    app_provider.tsx
    config/
      api.ts           # baseURL, timeouts, etc.
      feature_flags.ts
      theme.ts
  domain/
    common/
      errors.ts
      types.ts        # Frontend-only VOs (filters, preferences, etc.)
    auth/
      entities/
      value_objects/
      services/
      ports/
      exceptions/
    admin/
      entities/
      services/
      ports/
    subscription/
    dashboard/
    chat/
    # other contexts as they emerge
  application/
    common/
      ports/
      errors/
    auth/
      queries/
      commands/
      adapters/       # mappers DTO ⇄ entities/VOs
    admin/
      queries/
      commands/
    subscription/
    dashboard/
  infrastructure/
    http/
      http_client.ts   # wrapper over fetch/axios + interceptors
      error_mapping.ts
    storage/
      local_storage.ts
      session_storage.ts
    analytics/
      tracking_client.ts
    auth/
      token_provider.ts
      session_transport.ts
      adapters/
    admin/
      adapters/
    subscription/
      adapters/
  presentation/
    routes/
      index.tsx        # route tree by context
    pages/
      auth/
        LoginPage.tsx
        SignupPage.tsx
      dashboard/
        DashboardPage.tsx
      admin/
        AdminUsersPage.tsx
        AdminMetricsPage.tsx
    components/
      ui/
        Button.tsx
        Card.tsx
        Input.tsx
        LoadingScreen.tsx
      layout/
        Layout.tsx
      shared/
        ProtectedRoute.tsx
    layouts/
      AuthLayout.tsx
      AdminLayout.tsx
    i18n/
      # strings, namespaces per context
  lib/                  # pure utilities
  hooks/                # UI hooks (not use cases)
  contexts/             # cross-cutting providers (Auth, Theme, Analytics)
```

---

## 3. Mapping Current Code → Hexagonal Structure

### 3.1 Setup / Cross-cutting Infrastructure

- **`provider.tsx`**  
  - → `setup/app_provider.tsx`  
  - Assemble here: `Router`, `AuthProvider`, `QueryClientProvider` (if used), `ThemeProvider`, Analytics, etc.

- **`constants/theme.ts`**  
  - → `setup/config/theme.ts` or `presentation/theme/theme.ts`

- **`lib/api.ts`**  
  - → `infrastructure/http/http_client.ts`  
  - Encapsulate: baseURL (from `setup/config/api.ts`), common headers, error handling

- **`lib/errors.ts`**  
  - → `infrastructure/http/error_mapping.ts` and/or `domain/common/errors.ts` for domain errors

- **`hooks/useTracking.ts`**  
  - → if only talks to analytics: `infrastructure/analytics/tracking_client.ts` + thin hook in `hooks/useTracking.ts`

### 3.2 Domain / Application (Use Cases)

- **`types/auth.types.ts`**  
  - → `domain/auth/entities/User.ts` + `value_objects/AuthToken.ts`, etc.  
  - Keep these types free from React and HTTP; they represent the model the frontend handles for auth

- **`hooks/useAnvilAuth.ts`**  
  Mix of domain, application, and possibly infrastructure logic. Split into:

  - **Domain**: pure services (e.g., decide if a user has access to a section by role)  
    - → `domain/auth/services/AuthService.ts`
  - **Ports**: how the app talks to the backend  
    - → `domain/auth/ports/AuthQueryPort.ts`, `AuthCommandPort.ts`
  - **Application**: hooks/use cases that orchestrate calls  
    - → `application/auth/queries/useCurrentUser.ts`  
    - → `application/auth/commands/useLogin.ts`, `useLogout.ts`
  - **Infrastructure**: HTTP implementation of ports  
    - → `infrastructure/auth/adapters/AuthHttpAdapter.ts` that uses `http_client.ts`

- **`hooks/useSignup.ts`**  
  - → `application/auth/commands/useSignup.ts` (write use case)  
  - Internally depends on an `AuthCommandPort` that implements `signup` using HTTP

### 3.3 Presentation

- **`pages/LoginPage.tsx`, `SignupPage.tsx`**  
  - → `presentation/pages/auth/LoginPage.tsx`, `SignupPage.tsx`  
  - Each page:
    - Uses **application** hooks (`useLogin`, `useSignup`)
    - Doesn't make direct fetch calls or know about endpoints

- **`pages/DashboardPage.tsx`**  
  - → `presentation/pages/dashboard/DashboardPage.tsx`  
  - Depends on `application/dashboard/queries/*`

- **`AdminUsersPage.tsx`, `AdminMetricsPage.tsx`**  
  - → `presentation/pages/admin/AdminUsersPage.tsx`, `AdminMetricsPage.tsx`  
  - Depend on `application/admin/queries/*` and `commands/*`

- **`router.tsx`**  
  - → `presentation/routes/index.tsx`  
  - Define routes by context (`/auth`, `/admin`, `/dashboard`) and re-export an `AppRouter` used in `setup/app_provider.tsx`

- **`App.tsx`**  
  - Remains as minimal presentation entry, only mounting `AppProvider` + `AppRouter`

- **`components/*.tsx`**  
  - `Button`, `Card`, `Input`, `LoadingScreen` → `presentation/components/ui/*`  
  - `Layout` → `presentation/components/layout/Layout.tsx` or `presentation/layouts/MainLayout.tsx`  
  - `ProtectedRoute` → `presentation/components/shared/ProtectedRoute.tsx` (depends on `contexts/AuthContext` and/or `application/auth/queries`)

- **`contexts/AuthContext.tsx`**  
  - → `contexts/AuthContext.tsx` or `presentation/contexts/AuthContext.tsx` (as you prefer)  
  - Ideally delegates to use cases (`useCurrentUser`, `useLogin`, etc.), not direct HTTP

---

## 4. How to Migrate Without Breaking Anything

### Phase 1 – Infrastructure and Setup

1. **Create new directories** (`setup`, `infrastructure`, `presentation`, `domain`, `application`) without moving code yet
2. **Move only very low-risk items**:
   - `lib/api.ts` → `infrastructure/http/http_client.ts` (leave temporary re-export in `lib/api.ts`)
   - `constants/theme.ts` → `setup/config/theme.ts` (or re-export from old location)
3. **Configure aliases in `tsconfig`** (for future migrations):

   ```json
   {
     "compilerOptions": {
       "baseUrl": "src",
       "paths": {
         "@domain/*": ["domain/*"],
         "@application/*": ["application/*"],
         "@infrastructure/*": ["infrastructure/*"],
         "@presentation/*": ["presentation/*"],
         "@setup/*": ["setup/*"]
       }
     }
   }
   ```

   This way new modules can directly use `@infrastructure/http/http_client`

### Phase 2 – Auth as Pilot Context

1. **Extract auth types**:
   - Move `types/auth.types.ts` to `domain/auth/entities/` and `value_objects/`  
   - Leave an `export * from '@domain/auth/...'` in the old path to avoid breaking imports

2. **Define auth ports** (domain):

   ```ts
   // domain/auth/ports/AuthQueryPort.ts
   export interface AuthQueryPort {
     getCurrentUser(): Promise<User | null>;
   }

   // domain/auth/ports/AuthCommandPort.ts
   export interface AuthCommandPort {
     login(email: string, password: string): Promise<User>;
     logout(): Promise<void>;
     signup(input: SignupInput): Promise<User>;
   }
   ```

3. **Implement HTTP adapter**:

   ```ts
   // infrastructure/auth/adapters/AuthHttpAdapter.ts
   export class AuthHttpAdapter implements AuthQueryPort, AuthCommandPort {
     // uses http_client, maps DTO ⇄ entities
   }
   ```

4. **Create use cases (application hooks)**:

   ```ts
   // application/auth/commands/useLogin.ts
   export function useLogin(port: AuthCommandPort = authPortInstance) { ... }

   // application/auth/queries/useCurrentUser.ts
   export function useCurrentUser(port: AuthQueryPort = authPortInstance) { ... }
   ```

5. **Refactor `useAnvilAuth` and `useSignup`** to internally delegate to these hooks or remove them entirely and progressively update pages

6. **Update `AuthContext`** to depend on `useCurrentUser`/`useLogin`/`useLogout` and not direct `fetch`

7. Verify that `LoginPage`, `SignupPage`, `ProtectedRoute` still work

### Phase 3 – Admin, Dashboard and Other Contexts

- Repeat same pattern:
  - Define frontend-only **entities/VOs** where it makes sense (admin table filters, etc.)
  - Define **ports** (`AdminUserQueryPort`, `SubscriptionQueryPort`, etc.)
  - Implement **HTTP adapters** in `infrastructure/{context}/adapters`
  - Create **queries/commands** in `application/{context}`
  - Connect **pages** in `presentation/pages/{context}` to those use cases

### Phase 4 – Cleanup and Rule Enforcement

- When all critical code uses the new structure:
  - Remove old re-exports
  - Add ESLint / TS rules to:
    - Prohibit `presentation` from importing directly from `infrastructure` (only via `application`/`domain`)
    - Prohibit `domain` from importing `react`, `axios`, etc.
- Document in `anvil_frontend/TASKS/` the flow "how to add a new context" following the same schema as the backend

---

## 5. Quick Summary

- **Backend** is already a clear example of hexagonal by layers and contexts; we're going to replicate those principles in the frontend
- I proposed a **target `src/` structure** with `setup`, `domain`, `application`, `infrastructure`, `presentation` and mapped **each current file** to its destination layer
- The plan is **incremental**: first move infrastructure/config, then use **auth** as pilot context (ports + adapters + use cases), then extend to admin/dashboard and finally cleanup aliases and enforce rules
- If you want, in the next message I can go into detail on one context (e.g., `auth`) with concrete code for interfaces, HTTP adapter, and application hooks ready to copy
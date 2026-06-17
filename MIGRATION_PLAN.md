# Migration Plan: WinForms → Angular + Spring Boot

App modernization of the **Employee Search** application. The goal is a **functional
migration** (full feature parity) from the current .NET 8 WinForms desktop app to a
three-tier web stack — **Angular** frontend, **Java / Spring Boot** REST backend, and a
**swappable relational database**.

---

## 1. Goals

1. **Migrate all existing functionality** to the new stack with no feature loss.
2. **Database swappability** — develop against a simple DB now, and later point at a real
   database by supplying credentials via configuration only (no code changes, no rebuild).

---

## 2. Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Database (now) | **H2 in-memory**, seeded on startup | Zero install; fast to stand up for the POC |
| Database (later) | Any JDBC database via **Spring profiles + env-var credentials** | All access via JPA, so queries are DB-agnostic |
| Authentication | Start with a **simple login endpoint**; defer JWT-vs-session | Keep auth isolated so it can be hardened later |
| CSV export | **Client-side** in Angular | Avoids an extra endpoint; mirrors current behavior |
| Migration style | **Functional rewrite**, not a UI port | Modernization, not mechanical translation |

---

## 3. Feature Inventory (what must be preserved)

| Feature | Current location | Behavior |
|---------|------------------|----------|
| Login w/ BCrypt | `Database/DatabaseHelper.cs:99` (`ValidateLogin`) | Validate username/password against stored hash |
| Employee search | `Database/DatabaseHelper.cs:110` (`SearchEmployees`) | Name partial match (case-insensitive); department, role, status exact match; any combination |
| Data model | `Models/Employee.cs` | 9 fields: Id, Name, Department, Role, Status, Email, Phone, HireDate, Salary |
| DB init + seed | `Database/DatabaseHelper.cs:12` (`Initialize`) | Create tables; seed admin user + 15 employees |
| CSV export | `Views/SearchForm.cs:54` (`btnExport_Click`) | Export currently filtered rows; RFC-style quoting |
| Status color badges | `Views/SearchForm.cs:124` (`CellFormatting`) | Active = green, Inactive = red, On Leave = amber |
| Login UI | `Views/LoginForm.cs` | Form + inline error messaging |
| Search UI | `Views/SearchForm.cs` | Filter panel, results grid, Search / Clear / Export / Logout |

**Filter values:** Department (IT, HR, Finance, Marketing, Operations) · Role (Analyst,
Coordinator, Designer, Developer, Manager) · Status (Active, Inactive, On Leave).

**Default login:** `admin` / `admin123` (BCrypt work factor 11).

---

## 4. Architectural Shift

Today the UI calls the database directly (`DatabaseHelper` invoked straight from the
forms) in a single process. The new stack splits into three tiers:

```
┌──────────────┐      HTTP/JSON      ┌──────────────────┐      JPA/JDBC      ┌────────────┐
│   Angular    │ ──────────────────► │   Spring Boot    │ ─────────────────► │  Database  │
│  (browser)   │ ◄────────────────── │   REST API       │ ◄───────────────── │ (swappable)│
└──────────────┘                     └──────────────────┘                    └────────────┘
   UI + routing                      auth, search, seed                      H2 now / real later
```

The UI no longer touches the DB; everything goes through REST endpoints.

---

## 5. Target Project Structure

```
MT_POC2/
├── backend/                      # Spring Boot (Java 17+, Maven)
│   ├── pom.xml
│   └── src/main/
│       ├── java/com/example/employeesearch/
│       │   ├── EmployeeSearchApplication.java
│       │   ├── model/        Employee.java, User.java
│       │   ├── repository/   EmployeeRepository, UserRepository
│       │   ├── service/      EmployeeService, AuthService
│       │   ├── controller/   EmployeeController, AuthController
│       │   ├── dto/          LoginRequest, EmployeeFilter
│       │   └── config/       SecurityConfig, CorsConfig, DataSeeder
│       └── resources/
│           ├── application.properties        # shared; selects active profile
│           ├── application-dev.properties     # H2 (now)
│           └── application-prod.properties     # real DB via env vars (later)
└── frontend/                     # Angular
    └── src/app/
        ├── login/        login.component
        ├── search/       search.component
        ├── services/     auth.service, employee.service
        ├── models/       employee.ts
        └── guards/       auth.guard
```

---

## 6. Backend Tasks (Spring Boot)

| # | Task | Replaces |
|---|------|----------|
| B1 | Scaffold via Spring Initializr: **Spring Web, Spring Data JPA, Spring Security, H2, Lombok** | `EmployeeSearch.csproj` |
| B2 | `Employee` JPA entity (9 fields; drop `SalaryFormatted` — format in UI) + `User` entity | `Models/Employee.cs` |
| B3 | `EmployeeRepository` + JPA **Specifications** for the dynamic name/dept/role/status filter | `SearchEmployees` |
| B4 | `AuthService.validateLogin()` using Spring's `BCryptPasswordEncoder` | `ValidateLogin` |
| B5 | `DataSeeder` (`CommandLineRunner`, **dev profile only**) — admin user + 15 employees | `Initialize` / `SeedEmployees` |
| B6 | `EmployeeController`: `GET /api/employees?name=&department=&role=&status=` | search form wiring |
| B7 | `AuthController`: `POST /api/auth/login` (auth logic isolated for later JWT/session) | login form wiring |
| B8 | (Optional) CSV export endpoint — default is client-side in Angular (F7) | `BuildCsv` |
| B9 | `CorsConfig` allowing `localhost:4200`; profile-based `application*.properties` | — (new) |

---

## 7. Frontend Tasks (Angular)

| # | Task | Replaces |
|---|------|----------|
| F1 | `ng new frontend` + **Angular Material** | — |
| F2 | `login.component` — form, calls `/api/auth/login`, shows error text | `Views/LoginForm.cs` |
| F3 | `search.component` — name input + 3 dropdowns + Search / Clear buttons | filter panel in `SearchForm` |
| F4 | `mat-table` results; status badge colors via CSS class binding | `DataGridView` + `CellFormatting` |
| F5 | `employee.service` + `auth.service` (HttpClient) | direct `DatabaseHelper` calls |
| F6 | `auth.guard` — redirect to login if not authenticated | implicit form-open gate |
| F7 | Client-side CSV download of current results | `btnExport_Click` |

---

## 8. Database Swappability (key requirement)

All data access goes through **JPA / Hibernate**, not raw SQL strings, so the same
queries run unchanged across H2, PostgreSQL, MySQL, SQL Server, and Oracle — Hibernate
generates the correct dialect.

Switching databases is a **configuration change only**, via Spring profiles:

`application-dev.properties` (used now):
```properties
spring.datasource.url=jdbc:h2:mem:employeesearch
spring.datasource.username=sa
spring.datasource.password=
spring.jpa.hibernate.ddl-auto=create-drop
spring.h2.console.enabled=true
```

`application-prod.properties` (used later — credentials from environment, never committed):
```properties
spring.datasource.url=${DB_URL}
spring.datasource.username=${DB_USER}
spring.datasource.password=${DB_PASSWORD}
spring.datasource.driver-class-name=${DB_DRIVER}
spring.jpa.hibernate.ddl-auto=validate
```

To point at a real database later:
1. Add that database's JDBC driver to `pom.xml` (one dependency).
2. Set the environment variables: `DB_URL`, `DB_USER`, `DB_PASSWORD`, `DB_DRIVER`.
3. Run with `--spring.profiles.active=prod`.

**Existing vs. empty target DB:** if the real DB already has data, use
`ddl-auto=validate` and skip seeding (the seeder is dev-profile only). If it starts
empty, let Hibernate create the schema and run a one-time seed.

---

## 9. Things That Go Away

- Single `.exe` packaging → backend **JAR** (or container) + frontend **static bundle**.
- `Program.cs` login/search loop → HTTP routing + Angular router.
- `*.Designer.cs` files → no equivalent; Angular templates are the UI.
- Direct DB calls from the UI → all access via REST + JPA.

---

## 10. New Concerns Introduced by the Web Stack

- **Auth token** — desktop had an implicit in-process session; web needs JWT or a session
  cookie (deferred, but designed for).
- **CORS** — Angular dev server must be allowed to call the API.
- **Two processes** — `mvn spring-boot:run` + `ng serve` (was a single `dotnet run`).
- **HTTPS / token expiry** — production hardening, new surface area.

---

## 11. Recommended Build Order

1. **Backend B1–B5** → verify seed data via the H2 console.
2. **Backend B6–B9** → test endpoints with curl / Postman.
3. **Frontend F1–F5** → wire to the live API.
4. **Frontend F6–F7** → route guard + CSV export polish.
5. **Defer auth hardening** (JWT / session) until the end-to-end flow works.

---

## 12. Tech Stack Mapping (reference)

| Concern | Current (.NET) | New (Java/Angular) |
|---------|----------------|--------------------|
| UI | WinForms | Angular + Angular Material |
| Results grid | `DataGridView` | `mat-table` |
| Password hashing | `BCrypt.Net-Next` | Spring Security `BCryptPasswordEncoder` |
| DB access | `Microsoft.Data.Sqlite` (raw SQL) | Spring Data JPA / Hibernate |
| Dynamic filters | Hand-built `WHERE` clause | JPA `Specification` |
| DB | SQLite file | H2 (now) → any JDBC DB (later) |
| Entry point | `Program.cs` | `EmployeeSearchApplication.java` + Angular router |
| Build / run | `dotnet run` | `mvn spring-boot:run` + `ng serve` |
| Packaging | Single `.exe` | JAR/container + static frontend bundle |

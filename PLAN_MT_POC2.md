# Build Plan — EmployeeSearch (MT_POC2)

**Inputs:** `DESIGN_MT_POC2.md` (authoritative contracts) · `REQUIREMENTS_MT_POC2.md` (intent/values).
**Stack:** Angular 17 + Material · Java 17+/Spring Boot 3.3 (Maven, Spring Data JPA, Web, Security) · existing SQLite DB reused as-is (C1).

**Environment notes (this machine):**
- JDK: `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot` (Java 21 — satisfies Java 17+).
- Maven: downloaded to `D:\tools\apache-maven-3.9.9` (not previously installed).
- Existing DB: `bin/Debug/net8.0-windows/employeesearch.db` → used as `DB_PATH` for the C1 validate smoke test.
- Layout: `backend/` (Spring Boot), `frontend/` (Angular).

---

## Phase 1 — Setup
| Task | Scope | Implements | Acceptance |
|---|---|---|---|
| T1.1 | Spring Boot Maven project: `pom.xml` (web, data-jpa, security, validation, sqlite-jdbc, hibernate-community-dialects, jjwt, test), `application.yml` + `dev`/`prod` overlays | §3.1, §11.1, §2.3 | `mvn compile` succeeds |
| T1.2 | Angular 17 standalone app shell + routing skeleton | §6.1, §3.2 | `ng build` succeeds |

## Phase 2 — Data layer (C1)
| Task | Scope | Implements | Acceptance |
|---|---|---|---|
| T2.1 | `User`, `Employee` JPA entities mapped to `Users`/`Employees` with exact column casing | §4.2 | entities compile |
| T2.2 | `UserRepository`, `EmployeeRepository` (+`JpaSpecificationExecutor`) | §5.5 | repos compile |
| T2.3 | **Validate mapping against real DB** (`ddl-auto=validate`, `DB_PATH`→existing file); resolve R-1 if it surfaces | §4.3, §4.4, C1 | app context loads against real DB; data layer test green |

## Phase 3 — Auth seam (C2)
| Task | Scope | Implements | Acceptance |
|---|---|---|---|
| T3.1 | `AuthenticationProvider` interface + `AuthenticatedUser`; `DbAuthenticationProvider` dev stub (BCrypt, case-sensitive username); `AdAuthenticationProvider` placeholder `TODO (AD)` | §7.1, C2 | stub verifies existing `$2a$11$` hash |
| T3.2 | `JwtService` + `JwtAuthFilter`; `SecurityConfig` (stateless, login permitAll, rest authenticated, `@PreAuthorize`) | §7.2 | secured endpoints 401 without token |
| T3.3 | CORS config (profile-driven origins) | §9 | preflight allowed for Angular origin |

## Phase 4 — Backend features
| Task | Scope | Implements | Acceptance |
|---|---|---|---|
| T4.1 | DTOs: `LoginRequest/Response`, `EmployeeDto`, `EmployeeSearchCriteria`, `FilterOptionsDto` | §5.3 | — |
| T4.2 | `AuthService` + `AuthController` A1/A2; `GlobalExceptionHandler` (RFC7807) | §5.2, §5.7, §10.1 | login 200/400/401 per BR-3 |
| T4.3 | `EmployeeSpecifications` + `EmployeeService` (BR-4 predicate, single source) | §5.4, §5.5 | unit tests for filter combos |
| T4.4 | `EmployeeController` E1 + `MetaController` M1 | §5.2 | sorted results; filter options w/ `All` |
| T4.5 | `CsvExportService` (BR-8 quoting, EXP-1 order, raw salary, CRLF, no BOM) + E2 endpoint + empty guard (409, BR-7) | §5.4, EXP-1, BR-7/8 | CSV byte expectations; 409 on empty |
| T4.6 | Audit logging (login/search/export) | §9 | log lines present |

## Phase 5 — Frontend
| Task | Scope | Implements | Acceptance |
|---|---|---|---|
| T5.1 | `AuthService`, `authInterceptor`, `authGuard`, models | §6.4, §6.1 | guard blocks `/search` |
| T5.2 | `LoginComponent` (gradient, validation, error states; no creds hint) | §6.2, UI-1, SEC-1 | login flow works |
| T5.3 | `EmployeeService` (search/export/filters) | §6.4 | — |
| T5.4 | `SearchComponent` (header, filters from M1, mat-table w/ status colors + currency, status bar, Clear, Export download) | §6.3, UI-2, BR-5/6 | all screen behaviors |

## Phase 6 — Cross-cutting & e2e
| Task | Scope | Implements | Acceptance |
|---|---|---|---|
| T6.1 | Backend `mvn test` green; frontend builds | DoD | tests pass |
| T6.2 | E2e: start backend on real DB, login as admin, search, export | §14.3 | endpoints verified live |

## Out of scope (per design §1.2)
User management, employee CRUD, role-based field restrictions, account lockout, live AD wiring, DB seeding.

## Open items
- OQ-5: CSV emits **no BOM** (design decision). OQ-7: filename uses server local time. R-2/OQ-4: native `LIKE` semantics preserved (not "fixed").

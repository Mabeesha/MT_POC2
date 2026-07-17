# Requirements Specification — EmployeeSearch (MT_POC2)

**Document version:** 1.0  
**Extracted from:** `D:\career\projects\MT_POC2` (read-only survey, no source changes)  
**Scope:** Technology-neutral description of what the application does.  
**Exclusions:** `AgentInstructionSet/` and `AgentInstructionSet2/` directories were not read.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Functional Requirements](#2-functional-requirements)
3. [UI / Screens](#3-ui--screens)
4. [Data Model](#4-data-model)
5. [Business Logic & Validation](#5-business-logic--validation)
6. [Data Access](#6-data-access)
7. [Auth / Authz / Security](#7-auth--authz--security)
8. [Integrations](#8-integrations)
9. [Background / Scheduled](#9-background--scheduled)
10. [Non-Functional](#10-non-functional)
11. [Reports & Exports](#11-reports--exports)
12. [Goes Away / New Concerns](#12-goes-away--new-concerns)
13. [Open Questions & Assumptions](#13-open-questions--assumptions)
14. [Traceability Index](#14-traceability-index)

---

## 1. System Overview

EmployeeSearch is a single-user Windows desktop application that gives authenticated staff members a searchable, filterable view of an employee directory. On startup the application initialises a local embedded database (creating tables and seeding reference data on first run), then presents a login screen; a successful login opens a search screen showing all employees. The user can narrow results with a name text filter and three dropdown filters (Department, Role, Status), export any visible result set to a CSV file, and log out to return to the login screen. The data store is a file-based relational database co-located with the executable; no network connectivity, external server, or installation procedure is required. There is currently a single hardcoded user account (`admin`); no user-management UI exists. The application has two screens (Login and Search) and no further navigation.

> Sources: `Program.cs:1–35`, `README.md`, `DOCUMENTATION.md:18–28`

---

## 2. Functional Requirements

### FR-1 — Application Startup & Database Initialisation

**Trigger:** The executable is launched.

**Flow:**
1. High-DPI awareness, visual styles, and GDI+ text rendering are configured.
2. `DatabaseHelper.Initialize()` is called once before any UI is shown.
3. The database file `employeesearch.db` is opened (or created) in the same directory as the executable.
4. Tables `Users` and `Employees` are created if they do not already exist (`CREATE TABLE IF NOT EXISTS`).
5. If no row with `Username = 'admin'` exists in `Users`, the admin seed account is inserted (see [BR-1](#br-1--admin-seed-account)).
6. If `Employees` contains zero rows, 15 seed employee records are inserted (see [Data Model §4.3](#43-seed-data--employees)).
7. The Login screen is displayed.

> `Program.cs:14–16`, `Database/DatabaseHelper.cs:13–39`

---

### FR-2 — User Login

**Trigger:** User submits the Login form (button click or Enter key in either field).

**Inputs:** Username (text), Password (text, masked).

**Flow:**
1. Username is trimmed of leading/trailing whitespace; password is taken as-is.
2. If either field is blank after trimming, show inline error `"Please enter both username and password."` and stop.
3. Query the `Users` table for the `PasswordHash` where `Username` matches the trimmed input.
4. If no matching row is found, or BCrypt verification of the supplied password against the stored hash fails, show inline error `"Invalid username or password. Please try again."`, clear the password field, return focus to the password field, and stop.
5. On success: store the username in memory, close the Login dialog with a success result, and open the Search screen.

**Branch — window closed without login:** If the user closes the Login window without a successful login, the application exits.

> `Views/LoginForm.cs:39–61`, `Database/DatabaseHelper.cs:99–108`

---

### FR-3 — Employee Search

**Trigger:** (a) Search screen opens (search executes immediately with no filters active), (b) user clicks "Search", (c) user presses Enter in the Name text field.

**Inputs:**

| Filter | Type | Match behaviour |
|---|---|---|
| Employee Name | Free text | Case-insensitive partial match (`LIKE %value%`) on the `Name` column |
| Department | Dropdown | Exact equality match on `Department` column; value `"All"` means no filter |
| Role | Dropdown | Exact equality match on `Role` column; value `"All"` means no filter |
| Status | Dropdown | Exact equality match on `Status` column; value `"All"` means no filter |

**Flow:**
1. Read current values from the four filter controls.
2. Build a parameterised SQL `SELECT` on `Employees`; append a `WHERE` clause only for filters that are non-empty and not `"All"`. Multiple active filters are combined with `AND`.
3. Results are sorted ascending by `Name`.
4. Bind result list to the results grid.
5. Update the status bar:
   - 0 results → `"No employees match the selected filters."`
   - 1 result → `"1 employee found."`
   - N > 1 results → `"N employees found."`

> `Views/SearchForm.cs:107–122`, `Database/DatabaseHelper.cs:110–163`

---

### FR-4 — Clear Filters

**Trigger:** User clicks "Clear".

**Flow:**
1. Name text field is cleared.
2. All three dropdowns are reset to index 0 (`"All"`).
3. Search is re-executed (FR-3 flow, returning all employees).

> `Views/SearchForm.cs:39–43`

---

### FR-5 — Export to CSV

**Trigger:** User clicks "Export".

**Pre-condition:** At least one row is currently displayed in the results grid.

**Flow:**
1. If `_currentResults` is empty, show a modal information dialog with title `"Export to CSV"` and message `"There are no rows to export."` and stop.
2. Open a Save File dialog filtered to `*.csv`. Default filename: `employees_<yyyyMMdd_HHmmss>.csv` (timestamp uses local time at the moment of the click).
3. If the user cancels the dialog, stop (no file is written).
4. Write the CSV to the chosen path in UTF-8 encoding.
5. Update the status bar to: `"Exported N employee(s) to <filename>.csv."`  
   (Singular/plural: `"employee"` when N = 1, `"employees"` when N > 1.)

**Output:** A UTF-8 CSV file. See [§11 Reports & Exports](#11-reports--exports) for column specification.

> `Views/SearchForm.cs:54–75`

---

### FR-6 — Logout

**Trigger:** User clicks "Logout".

**Flow:**
1. Set internal `LoggedOut` flag to `true`.
2. Close the Search screen.
3. Application loop detects `LoggedOut = true` → re-displays the Login screen.

**Branch — window closed via OS close button (×):** `LoggedOut` remains `false`; the application loop exits and the process terminates.

> `Views/SearchForm.cs:48–51`, `Program.cs:17–33`

---

### FR-7 — Login/Search Cycle

The application supports repeated logout-and-login cycles within a single process lifetime. After each logout the Login screen is re-displayed. A new instance of both the Login form and the Search form is created for each cycle. The cycle terminates when either:
- The Login window is closed without successful authentication, or
- The Search window is closed via the OS close button (not Logout).

> `Program.cs:17–33`

---

## 3. UI / Screens

### UI-1 — Login Screen

**Window title:** `Employee Search — Login`  
**Window size:** 420 × 520 px (fixed, non-resizable; no maximise or minimise box)  
**Startup position:** Centred on primary monitor  
**Background:** Diagonal linear gradient from `#1B2A4A` (top-left) to `#2B5278` (bottom-right) at 45°  
**Font:** Segoe UI 9pt (default for all controls unless overridden)

The visible content is contained in a white card panel (340 × 410 px, located at offset 40, 50 inside the form).

#### Field table

| Control | Type | Label text | Position in card | Notable properties |
|---|---|---|---|---|
| `lblIcon` | Label | `🔍` (U+1F50D) | Top, centred | Segoe UI Emoji 18pt; centred in 340 px width |
| `lblTitle` | Label | `Employee Search` | Below icon | Segoe UI 16pt Bold; colour `#1B2838`; auto-size, centred programmatically |
| `lblSubtitle` | Label | `Sign in to your account` | Below title | Segoe UI 9pt; colour `#6B7280`; auto-size, centred |
| `lblUsername` | Label | `Username` | y=144 | Segoe UI 9pt Bold; colour `#374151` |
| `txtUsername` | TextBox | — | y=164; 280 × 27 px | Segoe UI 10pt; receives initial focus on open |
| `lblPassword` | Label | `Password` | y=204 | Segoe UI 9pt Bold; colour `#374151` |
| `txtPassword` | TextBox | — | y=224; 280 × 27 px | Segoe UI 10pt; system password-char masking enabled |
| `lblError` | Label | *(dynamic)* | y=258; 280 × 34 px | Segoe UI 8.5pt; colour `#DC2626` (red); **hidden** until an error occurs |
| `btnLogin` | Button | `Sign In` | y=302; 280 × 42 px | Segoe UI 10.5pt Bold; background `#1B4F8A`; hover `#154080`; pressed `#0F3060`; white text; flat style, no border |
| `lblHint` | Label | `Default credentials: admin / admin123` | y=358 | Segoe UI 8pt; colour `#9CA3AF`; centred in card |

**Interactions:**
- Pressing Enter in either `txtUsername` or `txtPassword` triggers the same login attempt as clicking `btnLogin`.
- On failed login: error label becomes visible with the relevant message; password field is cleared and focused.
- On successful login: form closes and the Search screen opens.

> `Views/LoginForm.Designer.cs:27–151`, `Views/LoginForm.cs:1–68`

---

### UI-2 — Search Screen

**Window title:** `Employee Search`  
**Window size:** 1000 × 700 px (initial); minimum 800 × 560 px (resizable)  
**Startup position:** Centred on primary monitor  
**Background:** `#F3F4F6` (light grey)  
**Font:** Segoe UI 9pt

The screen is divided into four vertically-stacked zones:

#### Zone 1 — Header panel (dark navy `#1B2A4A`, 100 px tall, full width, docked top)

| Control | Type | Text | Notes |
|---|---|---|---|
| `lblHeaderTitle` | Label | `🔍  Employee Search` | Segoe UI 13pt Bold; white; left-aligned at x=20, y=35 |
| `lblUser` | Label | `Logged in as: <username>` | Colour `#93C5FD` (light blue); right-anchored; set on form open |
| `btnLogout` | Button | `Logout` | Top-right; 90 × 32 px; background `#F3F4F6`; colour `#374151`; flat |
| `btnExport` | Button | `📊  Export` | Below Logout; 130 × 32 px; background `#217346` (Excel green); white text; hover `#1A5C37`; pressed `#134628` |

#### Zone 2 — Filters panel (white background, 160 px tall, full width, docked top below header)

**Panel title label:** `Search Filters` (Segoe UI 10pt Bold, `#1F2937`)

| Control | Type | Label | Position | Values / Notes |
|---|---|---|---|---|
| `txtName` | TextBox | `Employee Name` | Row 1, x=20; 606 × 26 px | Segoe UI 10pt; receives focus on form load; Enter triggers search |
| `cboDepartment` | ComboBox (drop-down list) | `Department` | Row 1, x=640; 160 × 26 px | `All`, `Finance`, `HR`, `IT`, `Marketing`, `Operations`; default: `All` |
| `cboRole` | ComboBox (drop-down list) | `Role` | Row 1, x=814; 160 × 26 px | `All`, `Analyst`, `Coordinator`, `Designer`, `Developer`, `Manager`; default: `All` |
| `cboStatus` | ComboBox (drop-down list) | `Status` | Row 2, x=20; 160 × 26 px | `All`, `Active`, `Inactive`, `On Leave`; default: `All` |
| `btnSearch` | Button | `🔍  Search` | Row 2, right-anchored | 110 × 34 px; background `#1B4F8A`; white text |
| `btnClear` | Button | `Clear` | Row 2, right-anchored | 90 × 34 px; background `#F3F4F6`; colour `#374151` |

All dropdown lists use `DropDownList` style (user cannot type a free-form value).

#### Zone 3 — Results grid (fills remaining space, docked fill)

A read-only data grid with the following columns (all text-type, no inline editing, full-row selection, single-select, auto-sized proportionally by fill-weight):

| Column header | Data field | Fill weight | Notes |
|---|---|---|---|
| `#` | `Id` | 50 | Numeric identifier |
| `Name` | `Name` | 160 | |
| `Department` | `Department` | 130 | |
| `Role` | `Role` | 130 | |
| `Status` | `Status` | 100 | Color-coded cell (see below) |
| `Email` | `Email` | 180 | |
| `Phone` | `Phone` | 120 | |
| `Hire Date` | `HireDate` | 110 | Stored as text; displayed as-is |
| `Salary` | `SalaryFormatted` | 110 | Currency formatted, no decimals (e.g. `$85,000`), locale-dependent |

**Status cell colour coding:**

| Status value | Background | Foreground |
|---|---|---|
| `Active` | `#D1FAE5` (green tint) | `#065F46` (dark green) |
| `Inactive` | `#FEE2E2` (red tint) | `#991B1B` (dark red) |
| `On Leave` | `#FEF3C7` (amber tint) | `#92400E` (dark amber) |
| *(other / unknown)* | `#E5E7EB` (grey) | `#374151` (dark grey) |

Grid properties: no add/delete/row-resize by user; row height 36 px; header height 38 px; alternating row background `#FAFAFA`; selection background `#DBEAFE`, foreground `#1E3A5F`; grid line colour `#F3F4F6`.

#### Zone 4 — Status bar (light grey `#E5E7EB`, 34 px tall, docked bottom)

Single label (`lblStatus`). Default text on first open: `"Use filters above and click Search to find employees."` Updated by every search and export action (see FR-3, FR-5).

> `Views/SearchForm.Designer.cs:38–300`, `Views/SearchForm.cs:1–144`

---

## 4. Data Model

### 4.1 Table: `Users`

> `Database/DatabaseHelper.cs:19–23`

| Column | Type | Nullable | Constraints | Notes |
|---|---|---|---|---|
| `Id` | `INTEGER` | NOT NULL | `PRIMARY KEY AUTOINCREMENT` | Surrogate key |
| `Username` | `TEXT` | NOT NULL | `UNIQUE` | Case-sensitivity depends on SQLite collation (default: BINARY — case-sensitive) |
| `PasswordHash` | `TEXT` | NOT NULL | — | BCrypt hash string (e.g. `$2a$11$...`) |

**Indexes:** The `UNIQUE` constraint on `Username` implicitly creates a unique index.

**Relationships:** None (no foreign keys referencing this table from `Employees`).

**JPA mapping notes:**
- `INTEGER PRIMARY KEY AUTOINCREMENT` maps cleanly to `@GeneratedValue(strategy = GenerationType.IDENTITY)`.
- `Username UNIQUE` → `@Column(unique = true)`.
- ASSUMPTION: SQLite's default case-sensitive collation on `Username` means `Admin` ≠ `admin`. The login query uses an exact equality match; the web replacement should preserve case-sensitive username comparison.

---

### 4.2 Table: `Employees`

> `Database/DatabaseHelper.cs:24–34`

| Column | Type | Nullable | Constraints | Notes |
|---|---|---|---|---|
| `Id` | `INTEGER` | NOT NULL | `PRIMARY KEY AUTOINCREMENT` | Surrogate key |
| `Name` | `TEXT` | NOT NULL | — | Full name, free text |
| `Department` | `TEXT` | NOT NULL | — | No FK; validated only at the UI layer |
| `Role` | `TEXT` | NOT NULL | — | No FK; validated only at the UI layer |
| `Status` | `TEXT` | NOT NULL | — | No FK; validated only at the UI layer |
| `Email` | `TEXT` | **NULL allowed** | — | Optional |
| `Phone` | `TEXT` | **NULL allowed** | — | Optional; stored as text (no format constraint in DB) |
| `HireDate` | `TEXT` | **NULL allowed** | — | ISO 8601 date string `YYYY-MM-DD` in seed data; no DB-level format constraint |
| `Salary` | `REAL` | **NULL allowed** | — | Floating-point; displayed as currency `C0` (no decimals) |

**Indexes:** Only the implicit primary key index.

**No foreign keys, triggers, stored procedures, computed columns, or check constraints** are defined on either table.

**JPA mapping notes:**
- `REAL` for `Salary` maps to `Double`/`double` or `BigDecimal`; using `BigDecimal` is recommended for monetary values to avoid floating-point rounding (ASSUMPTION — the existing schema uses `REAL`).
- `HireDate` stored as `TEXT` will need to be mapped as `String` initially or converted to `LocalDate` with a converter in the new stack.
- `Department`, `Role`, and `Status` are free text with no DB-level constraint; consider adding `CHECK` constraints or referencing lookup tables in the new schema.

---

### 4.3 Seed Data — `Users`

Inserted on first run if `Username = 'admin'` does not exist:

| Username | Password (plain) | PasswordHash |
|---|---|---|
| `admin` | `admin123` | BCrypt hash with work factor 11 (computed at runtime; value varies) |

> `Database/DatabaseHelper.cs:41–53`

**SECURITY FLAG:** The Login screen displays `"Default credentials: admin / admin123"` in plain text (`lblHint`). This credential hint is visible to anyone who opens the application.

> `Views/LoginForm.Designer.cs:140–145`

---

### 4.4 Seed Data — `Employees`

Inserted on first run if `Employees` table is empty (15 rows):

| Id (auto) | Name | Department | Role | Status | Email | Phone | HireDate | Salary |
|---|---|---|---|---|---|---|---|---|
| 1 | Alice Johnson | IT | Developer | Active | alice@corp.com | 555-0101 | 2021-03-15 | 85000 |
| 2 | Bob Smith | HR | Manager | Active | bob@corp.com | 555-0102 | 2019-07-01 | 92000 |
| 3 | Carol White | Finance | Analyst | Active | carol@corp.com | 555-0103 | 2020-11-20 | 78000 |
| 4 | David Brown | Marketing | Coordinator | On Leave | david@corp.com | 555-0104 | 2022-01-10 | 65000 |
| 5 | Eva Martinez | IT | Developer | Active | eva@corp.com | 555-0105 | 2021-08-05 | 88000 |
| 6 | Frank Lee | Operations | Manager | Active | frank@corp.com | 555-0106 | 2018-05-22 | 95000 |
| 7 | Grace Kim | HR | Analyst | Inactive | grace@corp.com | 555-0107 | 2020-04-17 | 72000 |
| 8 | Henry Davis | Finance | Manager | Active | henry@corp.com | 555-0108 | 2017-09-30 | 105000 |
| 9 | Irene Wilson | IT | Designer | Active | irene@corp.com | 555-0109 | 2023-02-14 | 80000 |
| 10 | Jack Taylor | Marketing | Manager | Active | jack@corp.com | 555-0110 | 2019-12-01 | 98000 |
| 11 | Karen Anderson | Operations | Coordinator | Active | karen@corp.com | 555-0111 | 2022-06-28 | 62000 |
| 12 | Liam Thompson | IT | Analyst | On Leave | liam@corp.com | 555-0112 | 2021-05-19 | 82000 |
| 13 | Maya Patel | Finance | Coordinator | Active | maya@corp.com | 555-0113 | 2023-08-07 | 60000 |
| 14 | Noah Garcia | Marketing | Designer | Active | noah@corp.com | 555-0114 | 2022-10-03 | 74000 |
| 15 | Olivia Chen | Operations | Analyst | Inactive | olivia@corp.com | 555-0115 | 2020-07-25 | 70000 |

> `Database/DatabaseHelper.cs:55–97`

**Observed domain values in seed data:**

| Attribute | Values present in seed data |
|---|---|
| Department | `Finance`, `HR`, `IT`, `Marketing`, `Operations` |
| Role | `Analyst`, `Coordinator`, `Designer`, `Developer`, `Manager` |
| Status | `Active`, `Inactive`, `On Leave` |

These match exactly the dropdown options in the Search screen filters.

---

### 4.5 Relationships

No foreign-key relationships are defined in the schema. The `Users` and `Employees` tables are independent.

---

## 5. Business Logic & Validation

### BR-1 — Admin Seed Account

If the `Users` table contains no row with `Username = 'admin'` at startup, one is inserted. The password `admin123` is hashed using BCrypt with work factor 11. The seed is idempotent: it does not re-insert if the row already exists.

> `Database/DatabaseHelper.cs:41–53`

---

### BR-2 — Employee Seed Data

If the `Employees` table contains zero rows at startup, 15 predefined records are inserted (see §4.4). The seed is idempotent: if any rows exist the seed is skipped entirely (even if fewer than 15 rows are present).

> `Database/DatabaseHelper.cs:55–97`

**FLAG:** The seed guard checks `COUNT(*) > 0` on the whole table, not for specific named records. If any employee rows exist (e.g. added manually), the 15 seed records will never be inserted, even if they are absent.

---

### BR-3 — Login Validation Rules

1. Username must be non-blank after trimming whitespace.
2. Password must be non-blank (no trimming applied to password).
3. Username must match an existing `Users.Username` value (case-sensitive, BINARY collation in SQLite).
4. The supplied plain-text password must verify against the stored BCrypt hash via `BCrypt.Verify`.
5. If rule 1 or 2 fails: display `"Please enter both username and password."`.
6. If rule 3 or 4 fails: display `"Invalid username or password. Please try again."` and clear the password field.
7. Rules 3 and 4 failures produce the same message intentionally (prevents username enumeration).

> `Views/LoginForm.cs:39–56`, `Database/DatabaseHelper.cs:99–108`

---

### BR-4 — Employee Search Filter Logic

Filters combine with logical AND. Each filter is applied only if its value is non-null, non-whitespace, and (for dropdowns) not equal to `"All"`.

| Filter | SQL operator | Value transformation |
|---|---|---|
| Name | `LIKE @name` | Value wrapped as `%<trimmed input>%` |
| Department | `= @dept` | Exact value from dropdown |
| Role | `= @role` | Exact value from dropdown |
| Status | `= @status` | Exact value from dropdown |

When no filters are active, the query is `SELECT … FROM Employees ORDER BY Name` (returns all rows).

> `Database/DatabaseHelper.cs:116–145`

**OPEN QUESTION:** SQLite's `LIKE` operator is case-insensitive for ASCII characters by default but case-sensitive for non-ASCII (Unicode) characters. Whether this is intentional for names with non-ASCII characters is not documented in the source.

---

### BR-5 — Status Colour Mapping

Applied per-cell in the results grid's Status column:

| Status value | Background hex | Foreground hex |
|---|---|---|
| `Active` | `#D1FAE5` | `#065F46` |
| `Inactive` | `#FEE2E2` | `#991B1B` |
| `On Leave` | `#FEF3C7` | `#92400E` |
| *(any other value)* | `#E5E7EB` | `#374151` |

> `Views/SearchForm.cs:124–143`

---

### BR-6 — Salary Display Format

`Salary` (stored as a floating-point number) is displayed in the grid using the format specifier `"C0"`: locale-aware currency symbol, no decimal places (e.g. `$85,000` on a US locale). The raw numeric value (e.g. `85000`) is used in CSV exports.

> `Models/Employee.cs:14`, `Views/SearchForm.Designer.cs:285`

**FLAG:** Using `double`/`REAL` for monetary values risks floating-point rounding artefacts. This is a known awkwardness for JPA mapping; `BigDecimal` should be considered in the new stack.

---

### BR-7 — Export Guard

Export is blocked (modal information dialog shown, no file written) when the current result set is empty.

> `Views/SearchForm.cs:55–61`

---

### BR-8 — CSV Field Quoting

A CSV field is wrapped in double-quotes if it contains any of: a comma (`,`), a double-quote (`"`), or a newline (`\n`). Internal double-quotes within a quoted field are escaped by doubling (`"` → `""`). Fields not meeting these conditions are written as-is (no quoting).

> `Views/SearchForm.cs:99–105`

---

### BR-9 — Logout vs. Window Close

Closing the Search screen via the OS "×" button is treated as an application exit (not a logout). Only clicking the "Logout" button returns the user to the Login screen.

> `Program.cs:30–33`, `Views/SearchForm.cs:48–51`

---

### BR-10 — Dropdown Values Are Fixed

The Department, Role, and Status dropdowns are populated with fixed string literals at form initialisation. Users cannot type free-form values. The values must match the corresponding column values in `Employees` for filters to return results.

> `Views/SearchForm.Designer.cs:180–207`

---

## 6. Data Access

### 6.1 Technology

Raw ADO.NET (no ORM). All database calls are made via `Microsoft.Data.Sqlite` (version 8.0.0). All queries are parameterised; no string concatenation of user input into SQL.

> `EmployeeSearch.csproj:13`, `Database/DatabaseHelper.cs:1–164`

---

### 6.2 Connection Management

A new `SqliteConnection` is opened and disposed (via `using`) for each database operation. There is no connection pool configuration, no shared long-lived connection, and no explicit transaction.

> `Database/DatabaseHelper.cs:14`, `99–101`, `112–113`

---

### 6.3 Queries Inventory

| Method | SQL pattern | Parameters | Returns |
|---|---|---|---|
| `Initialize` | `CREATE TABLE IF NOT EXISTS Users (...)` | none | void |
| `Initialize` | `CREATE TABLE IF NOT EXISTS Employees (...)` | none | void |
| `SeedAdminUser` | `SELECT COUNT(*) FROM Users WHERE Username = 'admin'` | none (literal) | scalar long |
| `SeedAdminUser` | `INSERT INTO Users (Username, PasswordHash) VALUES ('admin', @hash)` | `@hash` | void |
| `SeedEmployees` | `SELECT COUNT(*) FROM Employees` | none | scalar long |
| `SeedEmployees` | `INSERT INTO Employees (...) VALUES (@n, @d, @r, @s, @e, @p, @h, @sal)` ×15 | 8 params per row | void |
| `ValidateLogin` | `SELECT PasswordHash FROM Users WHERE Username = @u` | `@u` | scalar string |
| `SearchEmployees` | `SELECT Id,Name,Department,Role,Status,Email,Phone,HireDate,Salary FROM Employees [WHERE ...] ORDER BY Name` | 0–4 params | `List<Employee>` |

---

### 6.4 Dynamic Query Construction (SearchEmployees)

The `WHERE` clause is built at runtime by conditionally appending clause fragments to a `List<string>` and joining them with `" AND "`. The command parameters are bound before the `CommandText` is assigned. This is parameterised despite being dynamic: user input is never concatenated into the SQL string.

> `Database/DatabaseHelper.cs:116–145`

---

### 6.5 Transactions

No explicit transactions are used. Each insert in `SeedEmployees` is a separate auto-committed statement. The 15 seed inserts are not atomic: if the process is interrupted mid-seed, a partial set of employees will exist.

**FLAG:** This is a potential data-consistency issue during first-run seeding.

---

### 6.6 Concurrency

No locking, optimistic concurrency, or read-after-write consistency mechanism exists. The application is designed for a single concurrent user (desktop, single process). Multi-user access to the same `employeesearch.db` file is not addressed.

---

### 6.7 Caching

No in-memory caching. Every search operation issues a fresh SQL query to the database.

---

## 7. Auth / Authz / Security

### 7.1 Authentication

**Method:** Username + password, verified against a local `Users` table.

**Password storage:** BCrypt via `BCrypt.Net-Next 4.0.3`. Work factor: 11 (2^11 = 2048 iterations). Plain-text password is never stored or logged.

**Session:** No token, cookie, or session object. After login, only the `username` string is retained in memory and passed to the Search form constructor. There is no session expiry or timeout.

**TODO (AD):** Replace the local `Users` table with Active Directory authentication. The `ValidateLogin` method should be replaced by an AD bind or LDAP query. The `Users` table may become redundant.

> `Database/DatabaseHelper.cs:99–108`, `Views/LoginForm.cs:39–61`

---

### 7.2 Authorisation

There is **one implicit role only**: `authenticated user`. Any user who successfully logs in has full access to all features (search all employees, export all data, view all salary information).

No role-based access control, no per-record permissions, no field-level restrictions are implemented.

**TODO (AD):** When migrating to Active Directory, map the single implicit role to an AD group (e.g. `EmployeeSearch-Users`). All future role/permission distinctions should be documented here as they are defined.

---

### 7.3 Security Risks

| ID | Risk | Location | Severity | Notes |
|---|---|---|---|---|
| SEC-1 | Default credentials displayed in UI | `Views/LoginForm.Designer.cs:145` | HIGH | `lblHint` shows `"Default credentials: admin / admin123"` permanently on the login screen, visible to anyone who opens the app |
| SEC-2 | Single hardcoded admin account | `Database/DatabaseHelper.cs:41–53` | MEDIUM | No user management UI; no way to change the admin password through the application |
| SEC-3 | No account lockout | `Views/LoginForm.cs:39–61` | MEDIUM | Unlimited login attempts; no rate-limiting or lockout after N failures |
| SEC-4 | No session expiry | `Program.cs`, `Views/SearchForm.cs` | LOW | Once logged in, the session never expires regardless of idle time |
| SEC-5 | Database file unencrypted | `Database/DatabaseHelper.cs:9–10` | MEDIUM | SQLite file at `AppDomain.CurrentDomain.BaseDirectory/employeesearch.db` is a plain, unencrypted file; anyone with filesystem access can read it |
| SEC-6 | Salary data exposed to all authenticated users | `Views/SearchForm.Designer.cs:285` | LOW | No field-level access control; all authenticated users see salary information |
| SEC-7 | Work factor 11 is adequate but not future-proofed | `Database/DatabaseHelper.cs:48` | INFO | BCrypt work factor is hardcoded; no mechanism to re-hash with higher cost |

---

## 8. Integrations

**None.** The application has no network calls, no external APIs, no email, no file-system integrations beyond the local SQLite database and the CSV export (a user-initiated file write to a user-chosen path). There are no queues, no web services, no SMTP, and no external authentication providers.

---

## 9. Background / Scheduled

**None.** There are no background threads, timers, scheduled jobs, or event listeners. All operations are synchronous and triggered by user interaction. The application runs on a single STA thread.

> `Program.cs:8` (`[STAThread]`)

---

## 10. Non-Functional

### 10.1 Performance

No explicit performance requirements are stated. With 15 seed rows and no pagination, performance is trivially satisfied. Any performance expectation beyond this is an **OPEN QUESTION**.

### 10.2 High-DPI Support

The application is declared `SystemAware` for High-DPI displays.

> `Program.cs:11`

### 10.3 Rendering

Visual styles (modern themed rendering) and GDI+ text rendering are enabled.

> `Program.cs:12–13`

### 10.4 Locale / Internationalisation

- Salary is formatted with `"C0"` which is locale-dependent (e.g. `$85,000` on US-English, `£85,000` on UK-English). The application makes no attempt to pin to a specific locale.
- No internationalisation or multi-language support is implemented.
- Date strings are stored and displayed as plain text (`YYYY-MM-DD`); no locale-aware date formatting is applied.

> `Models/Employee.cs:14`

### 10.5 Error Handling

No try/catch blocks exist in any source file. All exceptions (e.g. database I/O failure, file write failure on export) will propagate unhandled and crash the application with an unhandled-exception dialog.

**FLAG:** This is a reliability concern; the web replacement should implement proper error handling.

### 10.6 Logging / Auditing

No logging framework is used. No audit trail of logins, searches, or exports is recorded.

### 10.7 Deployment

- Single executable (`WinExe`, `OutputType`); can be published as a self-contained single-file executable.
- Target: Windows only (`net8.0-windows`).
- Runtime: .NET 8.
- No installer, no registry entries, no external configuration file.
- Database file is created automatically in the same directory as the executable on first run.

> `EmployeeSearch.csproj:4–6`, `README.md:22–26`

### 10.8 Resizability

- Login window: fixed size, non-resizable.
- Search window: resizable, minimum 800 × 560 px. Grid columns resize proportionally to fill available width.

> `Views/LoginForm.Designer.cs:45–46`, `Views/SearchForm.Designer.cs:68–69`, `Views/SearchForm.Designer.cs:257`

---

## 11. Reports & Exports

### EXP-1 — Employee CSV Export

**Trigger:** FR-5 (user clicks Export with at least one result row visible).

**Scope:** Exactly the rows currently displayed in the results grid (i.e., the rows that matched the last-executed search filters). Not necessarily all employees.

**File format:** UTF-8 CSV (no BOM implied by `Encoding.UTF8`; note: `System.Text.Encoding.UTF8` in .NET does include a BOM preamble by default — OPEN QUESTION: is the BOM intentional?).

**Filename default:** `employees_<yyyyMMdd_HHmmss>.csv` (local time at the moment of button click).

**File filter:** `"CSV files (*.csv)|*.csv"`.

**Content:**

| Column order | Header text | Source field | Notes |
|---|---|---|---|
| 1 | `Id` | `Employee.Id` | Integer |
| 2 | `Name` | `Employee.Name` | Text |
| 3 | `Department` | `Employee.Department` | Text |
| 4 | `Role` | `Employee.Role` | Text |
| 5 | `Status` | `Employee.Status` | Text |
| 6 | `Email` | `Employee.Email` | Text |
| 7 | `Phone` | `Employee.Phone` | Text |
| 8 | `HireDate` | `Employee.HireDate` | Text as stored (e.g. `2021-03-15`) |
| 9 | `Salary` | `Employee.Salary` | Raw numeric (e.g. `85000`), NOT the formatted currency string |

**Quoting rules (RFC 4180 partial):** Fields containing `,`, `"`, or `\n` are wrapped in double-quotes with internal double-quotes doubled. All other fields are unquoted.

**Line endings:** `Environment.NewLine` (via `StringBuilder.AppendLine`) — CRLF on Windows.

**Status bar update on success:** `"Exported N employee(s) to <filename>.csv."`

> `Views/SearchForm.cs:54–105`

---

## 12. Goes Away / New Concerns

### 12.1 What Does Not Carry Over to a Web Stack

| Item | Reason |
|---|---|
| `*.Designer.cs` files | WinForms designer-generated control layout files; no equivalent in a web stack |
| `[STAThread]` / STA threading model | Windows COM threading requirement; irrelevant in a server/web context |
| `Application.Run()` / message loop | WinForms event pump; web servers have their own request lifecycle |
| `Application.EnableVisualStyles()` | WinForms-specific OS theme integration |
| `FormBorderStyle`, `MaximizeBox`, `StartPosition` | Desktop window management properties |
| `LinearGradientBrush` / `OnPaintBackground` override | GDI+ custom painting; use CSS gradients |
| `DataGridView` with `CellFormatting` event | WinForms grid; use a web table/grid component |
| `SaveFileDialog` | OS file-picker dialog; web uses browser download API |
| `UseSystemPasswordChar` on TextBox | WinForms password masking; use `<input type="password">` |
| Single-process packaging (`.exe` next to `.db`) | Self-contained desktop deployment; web app uses separate DB server/container |
| `AppDomain.CurrentDomain.BaseDirectory` for DB path | Filesystem-relative DB path; not applicable when DB is a separate service |
| `while(true)` login/search loop | Desktop navigation pattern; web uses routing and session management |
| `LoggedOut` bool flag | Navigation mechanism; replaced by session invalidation / redirect |
| Direct UI-to-DB calls (no service layer) | `SearchForm` → `DatabaseHelper` directly; web stack needs a service/API layer |

---

### 12.2 New Concerns for the Web Stack

| Concern | Notes |
|---|---|
| Authentication tokens / sessions | No session management exists today; web requires JWT, cookies, or similar |
| CORS | Not applicable to desktop; required for browser-based clients hitting a separate API |
| Statelessness | Desktop holds `_currentResults` and `_username` in form fields; web API must be stateless or use session state |
| HTTPS / TLS | All data travels in-process today; web transport must be encrypted |
| Input validation on server side | Today, all validation is client-side (WinForms); web stack must validate on the API layer too |
| User management | No UI to create/edit/delete users; web replacement must define this scope |
| Role-based access control | Currently single-role; AD integration point (see §7.2) |
| Pagination | No pagination today (15 rows); a production employee directory will need server-side pagination |
| Concurrency / multi-user access | Desktop is single-user; web is inherently multi-user — DB and API must handle concurrent reads |
| Audit logging | No logging today; web replacement should log authentication events and data access |
| Database migration strategy | Schema is minimal; new stack should introduce formal migration tooling (e.g., Flyway/Liquibase) |
| CSV export in a browser context | No `SaveFileDialog`; use `Content-Disposition: attachment` HTTP response header |
| `Salary` type promotion | `REAL`/`double` → `BigDecimal` recommended for monetary values |
| `HireDate` type promotion | `TEXT` → proper `DATE`/`LocalDate` column recommended |

---

## 13. Open Questions & Assumptions

| ID | Type | Description |
|---|---|---|
| OQ-1 | OPEN QUESTION | Is the `admin` seed account intended to be the only user permanently, or should user management (create/edit/delete users) be part of the modernised application? |
| OQ-2 | OPEN QUESTION | What is the intended size of the real employee dataset? The current UI has no pagination; is infinite-scroll or server-side pagination required? |
| OQ-3 | OPEN QUESTION | Should the new application allow editing employee records, or is the directory read-only? No create/edit/delete functionality exists today. |
| OQ-4 | OPEN QUESTION | Is the `LIKE` case-insensitivity for ASCII characters (SQLite default) the intended search behaviour for names? Non-ASCII name characters will not be matched case-insensitively. |
| OQ-5 | OPEN QUESTION | Is the `Encoding.UTF8` BOM on CSV export intentional? (`System.Text.Encoding.UTF8` includes a BOM in .NET; `Encoding.UTF8` is the same as `new UTF8Encoding(encoderShouldEmitUTF8Identifier: true)`) |
| OQ-6 | OPEN QUESTION | Are `Department`, `Role`, and `Status` intended to be closed enumerations (i.e., the values in the dropdowns are the complete valid set), or could new values be added? Currently there is no lookup table. |
| OQ-7 | OPEN QUESTION | Should the export filename timestamp use UTC instead of local time? The current implementation uses `DateTime.Now` (local). |
| OQ-8 | OPEN QUESTION | Should all authenticated users see salary information, or should that be restricted to specific roles? |
| OQ-9 | OPEN QUESTION | The seed guard for employees checks `COUNT(*) > 0` on the whole table. If the production database is pre-populated, seeding is silently skipped. Is the seed data required in production, or only for development/testing? |
| OQ-10 | OPEN QUESTION | No connection string configuration file exists; the DB path is hardcoded relative to the executable. How should this be configured in the web deployment environment? |
| A-1 | ASSUMPTION | The five `Department` values, five `Role` values, and three `Status` values visible in the dropdowns represent the complete intended domain for those attributes, as they perfectly match the seed data. |
| A-2 | ASSUMPTION | `HireDate` values in the format `YYYY-MM-DD` are ISO 8601 dates and should be treated as date-only values (no time component). |
| A-3 | ASSUMPTION | `Salary` represents an annual figure in the currency of the deployment locale (no currency is explicitly stored). |
| A-4 | ASSUMPTION | Username comparison is case-sensitive (matching SQLite's BINARY collation default). The web replacement should preserve this behaviour unless explicitly changed. |
| A-5 | ASSUMPTION | The `Phone` column stores values in a `NNN-NNNN` format (as seen in seed data) but there is no format constraint in the database or application; any string is accepted. |

---

## 14. Traceability Index

| Requirement ID | Evidence location |
|---|---|
| FR-1 | `Program.cs:9–16`, `Database/DatabaseHelper.cs:13–39` |
| FR-2 | `Views/LoginForm.cs:39–61`, `Database/DatabaseHelper.cs:99–108` |
| FR-3 | `Views/SearchForm.cs:107–122`, `Database/DatabaseHelper.cs:110–163` |
| FR-4 | `Views/SearchForm.cs:39–43` |
| FR-5 | `Views/SearchForm.cs:54–75` |
| FR-6 | `Views/SearchForm.cs:48–51`, `Program.cs:30–33` |
| FR-7 | `Program.cs:17–33` |
| UI-1 | `Views/LoginForm.Designer.cs:27–151`, `Views/LoginForm.cs:1–68` |
| UI-2 | `Views/SearchForm.Designer.cs:38–300`, `Views/SearchForm.cs:1–144` |
| UI-2 (Status colour) | `Views/SearchForm.cs:124–143` |
| Data Model — Users table | `Database/DatabaseHelper.cs:19–23` |
| Data Model — Employees table | `Database/DatabaseHelper.cs:24–34` |
| Data Model — Users seed | `Database/DatabaseHelper.cs:41–53` |
| Data Model — Employees seed | `Database/DatabaseHelper.cs:55–97` |
| BR-1 | `Database/DatabaseHelper.cs:41–53` |
| BR-2 | `Database/DatabaseHelper.cs:55–61` |
| BR-3 | `Views/LoginForm.cs:39–56`, `Database/DatabaseHelper.cs:99–108` |
| BR-4 | `Database/DatabaseHelper.cs:116–145` |
| BR-5 | `Views/SearchForm.cs:124–143` |
| BR-6 | `Models/Employee.cs:14`, `Views/SearchForm.Designer.cs:285` |
| BR-7 | `Views/SearchForm.cs:55–61` |
| BR-8 | `Views/SearchForm.cs:99–105` |
| BR-9 | `Program.cs:30–33`, `Views/SearchForm.cs:48–51` |
| BR-10 | `Views/SearchForm.Designer.cs:180–207` |
| SEC-1 | `Views/LoginForm.Designer.cs:145` |
| SEC-2 | `Database/DatabaseHelper.cs:41–53` |
| SEC-3 | `Views/LoginForm.cs:39–61` |
| SEC-4 | `Program.cs`, `Views/SearchForm.cs` |
| SEC-5 | `Database/DatabaseHelper.cs:9–10` |
| SEC-6 | `Views/SearchForm.Designer.cs:285` |
| SEC-7 | `Database/DatabaseHelper.cs:48` |
| EXP-1 | `Views/SearchForm.cs:54–105` |
| Non-Functional (HiDPI) | `Program.cs:11` |
| Non-Functional (deployment) | `EmployeeSearch.csproj:4–6`, `README.md:22–26` |
| Non-Functional (locale) | `Models/Employee.cs:14` |
| Non-Functional (resizability) | `Views/SearchForm.Designer.cs:68–70`, `Views/SearchForm.Designer.cs:257` |
| Employee model | `Models/Employee.cs:1–15` |
| Project definition | `EmployeeSearch.csproj:1–16` |
| Application entry point / loop | `Program.cs:1–35` |

---

*End of Requirements Specification — EmployeeSearch MT_POC2*

# Employee Search — Code Documentation

## Table of Contents

1. [Overview](#1-overview)
2. [Project Structure](#2-project-structure)
3. [Technology Stack](#3-technology-stack)
4. [Application Entry Point](#4-application-entry-point)
5. [Database Layer](#5-database-layer)
6. [Data Model](#6-data-model)
7. [Login Page](#7-login-page)
8. [Search Page](#8-search-page)
9. [End-to-End Application Flow](#9-end-to-end-application-flow)
10. [Security Design](#10-security-design)

---

## 1. Overview

Employee Search is a Windows desktop application built with **WPF (Windows Presentation Foundation)** on **.NET 8**. It provides two screens:

- A **login page** that authenticates users against a local database using hashed passwords.
- A **search page** where the authenticated user can filter and browse employee records using a combination of text input and dropdown filters.

The database is **SQLite**, an embedded file-based relational database. No server installation or network configuration is required — the database file (`employeesearch.db`) is created automatically the first time the app runs, alongside the executable.

---

## 2. Project Structure

```
MT_POC2/
├── EmployeeSearch.csproj       # Project definition: SDK, target framework, NuGet packages
├── App.xaml                    # WPF application root: declares the startup window
├── App.xaml.cs                 # Application startup code: initialises the database
├── AssemblyInfo.cs             # Auto-generated assembly metadata
│
├── Database/
│   └── DatabaseHelper.cs       # All database operations: init, login, search
│
├── Models/
│   └── Employee.cs             # C# class that represents one row from the Employees table
│
└── Views/
    ├── LoginWindow.xaml        # Login screen UI layout
    ├── LoginWindow.xaml.cs     # Login screen logic
    ├── SearchWindow.xaml       # Search screen UI layout
    └── SearchWindow.xaml.cs    # Search screen logic
```

---

## 3. Technology Stack

| Component | Technology | Version | Purpose |
|---|---|---|---|
| App framework | WPF (.NET) | .NET 8 | Windows desktop UI |
| Database | SQLite | via NuGet | Embedded relational database |
| SQLite driver | Microsoft.Data.Sqlite | 8.0.0 | ADO.NET provider for SQLite |
| Password hashing | BCrypt.Net-Next | 4.0.3 | Secure one-way password hashing |

### EmployeeSearch.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <UseWPF>true</UseWPF>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="BCrypt.Net-Next" Version="4.0.3" />
    <PackageReference Include="Microsoft.Data.Sqlite" Version="8.0.0" />
  </ItemGroup>
</Project>
```

Key settings explained:

- **`OutputType = WinExe`** — Builds a Windows GUI executable (no console window).
- **`TargetFramework = net8.0-windows`** — Targets .NET 8 with Windows-specific APIs enabled. The `-windows` suffix is required for WPF.
- **`Nullable = enable`** — The C# nullable reference types feature is turned on. This means the compiler warns you if you use a potentially-null variable without checking it first.
- **`ImplicitUsings = enable`** — Common namespaces like `System`, `System.Collections.Generic`, and `System.Linq` are auto-imported into every file, so you don't need to write `using System;` at the top of everything.
- **`UseWPF = true`** — Tells the SDK to include the WPF framework and enable `.xaml` file compilation.

---

## 4. Application Entry Point

### App.xaml

```xml
<Application x:Class="EmployeeSearch.App"
             xmlns="..."
             xmlns:x="..."
             StartupUri="Views/LoginWindow.xaml">
```

`App.xaml` is the root of every WPF application. The most important attribute here is `StartupUri`, which tells WPF which window to open when the application launches. Here it points to `LoginWindow.xaml`, making the login screen the first thing the user sees.

`x:Class="EmployeeSearch.App"` links this XAML file to its code-behind class, `App.xaml.cs`.

### App.xaml.cs

```csharp
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        DatabaseHelper.Initialize();
    }
}
```

`App` inherits from WPF's built-in `Application` class. By overriding `OnStartup`, we get a guaranteed hook that runs before any window is shown. This is the ideal place to perform one-time setup.

`DatabaseHelper.Initialize()` is called here to ensure the SQLite database file exists and the tables are created before the login window opens and tries to read from the database. If the app is run for the first time, this call creates the database from scratch and seeds it with data. On subsequent runs, it detects the tables already exist and does nothing.

---

## 5. Database Layer

**File:** `Database/DatabaseHelper.cs`

`DatabaseHelper` is a `static` class — it has no instance and all its methods are called directly, like `DatabaseHelper.Initialize()`. It is responsible for every interaction with the SQLite database.

### Database location

```csharp
private static readonly string DbPath = Path.Combine(
    AppDomain.CurrentDomain.BaseDirectory,
    "employeesearch.db"
);
private static string ConnectionString => $"Data Source={DbPath}";
```

`AppDomain.CurrentDomain.BaseDirectory` returns the folder where the compiled `.exe` lives (e.g., `bin\Debug\net8.0-windows\`). The database file is therefore placed in the same folder as the executable, making the application self-contained with no fixed installation path.

`ConnectionString` is a computed property (note the `=>` arrow) rather than a stored string, so it always reflects the current `DbPath` value.

### Initialize()

```csharp
public static void Initialize()
{
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();

    var cmd = conn.CreateCommand();
    cmd.CommandText = @"
        CREATE TABLE IF NOT EXISTS Users (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT NOT NULL UNIQUE,
            PasswordHash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Employees (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            ...
        );";
    cmd.ExecuteNonQuery();

    SeedAdminUser(conn);
    SeedEmployees(conn);
}
```

`using var conn` — The `using` keyword here ensures that the database connection is automatically closed and its resources released when execution leaves the block, even if an exception occurs. This is the standard safe pattern for working with database connections in .NET.

`CREATE TABLE IF NOT EXISTS` — This SQL clause means "only create the table if it doesn't already exist." This makes `Initialize()` safe to call on every startup: on the first run it creates the tables, on all subsequent runs it is a no-op.

**The two tables created:**

- **`Users`** — Stores login credentials. `Username` has a `UNIQUE` constraint, preventing duplicate accounts. `PasswordHash` stores the BCrypt hash of the password, never the plain text.
- **`Employees`** — Stores the employee records that are searched and displayed.

### SeedAdminUser(conn)

```csharp
private static void SeedAdminUser(SqliteConnection conn)
{
    var cmd = conn.CreateCommand();
    cmd.CommandText = "SELECT COUNT(*) FROM Users WHERE Username = 'admin'";
    var count = (long)(cmd.ExecuteScalar() ?? 0L);
    if (count > 0) return;

    var hash = BCrypt.Net.BCrypt.HashPassword("admin123");
    cmd = conn.CreateCommand();
    cmd.CommandText = "INSERT INTO Users (Username, PasswordHash) VALUES ('admin', @hash)";
    cmd.Parameters.AddWithValue("@hash", hash);
    cmd.ExecuteNonQuery();
}
```

This method inserts the default admin account only if it does not already exist (the `COUNT(*)` check). This prevents re-inserting the user on every startup.

`BCrypt.Net.BCrypt.HashPassword("admin123")` runs the BCrypt algorithm on the plain-text password and returns a string that looks like `$2a$11$...`. This hash is what gets stored in the database. The original password `admin123` is never stored anywhere.

`cmd.Parameters.AddWithValue("@hash", hash)` — The `@hash` is a **named parameter placeholder**. The actual value is bound separately by `AddWithValue`. This is parameterized querying, which prevents SQL injection (see [Security Design](#10-security-design)).

`ExecuteScalar()` returns the first column of the first row of the result. For a `COUNT(*)` query, this is a single integer. SQLite returns it as a `long` (64-bit integer), so the cast `(long)` is applied. The `?? 0L` handles the case where `ExecuteScalar()` returns `null` (e.g., on an empty table) by defaulting to zero.

### SeedEmployees(conn)

```csharp
private static void SeedEmployees(SqliteConnection conn)
{
    var cmd = conn.CreateCommand();
    cmd.CommandText = "SELECT COUNT(*) FROM Employees";
    var count = (long)(cmd.ExecuteScalar() ?? 0L);
    if (count > 0) return;

    var rows = new (string Name, string Dept, string Role, ...) []
    {
        ("Alice Johnson", "IT", "Developer", "Active", ...),
        ...
    };

    foreach (var r in rows)
    {
        var ins = conn.CreateCommand();
        ins.CommandText = @"INSERT INTO Employees (...) VALUES (@n, @d, @r, ...)";
        ins.Parameters.AddWithValue("@n", r.Name);
        ...
        ins.ExecuteNonQuery();
    }
}
```

Same guard-and-seed pattern as `SeedAdminUser`. The employee data is defined as an array of **C# value tuples** — a concise way to group related values without needing a full class. Each tuple holds all fields for one employee row. The `foreach` loop then inserts each tuple as a parameterized SQL statement.

### ValidateLogin(username, password)

```csharp
public static bool ValidateLogin(string username, string password)
{
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();
    var cmd = conn.CreateCommand();
    cmd.CommandText = "SELECT PasswordHash FROM Users WHERE Username = @u";
    cmd.Parameters.AddWithValue("@u", username);
    var hash = cmd.ExecuteScalar() as string;
    return hash != null && BCrypt.Net.BCrypt.Verify(password, hash);
}
```

This method performs login authentication in two steps:

1. **Lookup:** Query the database for the `PasswordHash` row where `Username` matches the input. If no row is found, `ExecuteScalar()` returns `null`, and the `as string` cast safely produces `null` (rather than throwing an exception).

2. **Verify:** `BCrypt.Net.BCrypt.Verify(password, hash)` re-runs the BCrypt algorithm on the plain-text input using the stored hash's embedded salt, and checks if the result matches. This is the correct way to verify BCrypt passwords — you cannot decrypt a BCrypt hash; you can only verify against it.

The method returns `false` in two cases: the username does not exist (`hash == null`), or the password does not match. Both cases produce the same generic error message in the UI, intentionally not revealing which one failed (this prevents username enumeration).

### SearchEmployees(name, department, role, status)

```csharp
public static List<Employee> SearchEmployees(
    string? name, string? department, string? role, string? status)
{
    var results = new List<Employee>();
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();

    var where = new List<string>();
    var cmd = conn.CreateCommand();

    if (!string.IsNullOrWhiteSpace(name))
    {
        where.Add("Name LIKE @name");
        cmd.Parameters.AddWithValue("@name", $"%{name.Trim()}%");
    }
    if (!string.IsNullOrWhiteSpace(department) && department != "All")
    {
        where.Add("Department = @dept");
        cmd.Parameters.AddWithValue("@dept", department);
    }
    // ... same pattern for role and status

    var sql = "SELECT Id, Name, ... FROM Employees";
    if (where.Count > 0)
        sql += " WHERE " + string.Join(" AND ", where);
    sql += " ORDER BY Name";

    cmd.CommandText = sql;
    using var reader = cmd.ExecuteReader();
    while (reader.Read())
    {
        results.Add(new Employee { Id = reader.GetInt32(0), ... });
    }
    return results;
}
```

This method builds a SQL query **dynamically** based on which filters have values. The approach works as follows:

- A `List<string>` called `where` accumulates SQL condition fragments (e.g., `"Name LIKE @name"`).
- For each filter that is non-empty and not set to `"All"`, a fragment is added to `where` and a corresponding parameter is added to the command.
- After all filters are checked, the fragments are joined with `" AND "` and appended to the base `SELECT` statement.
- If no filters are active, the `WHERE` clause is omitted entirely, returning all employees.

`LIKE @name` with the value `%alice%` performs a **case-insensitive partial match** — it finds any name that contains "alice" anywhere in it, regardless of capitalisation.

`reader.IsDBNull(5)` checks whether a column value is `NULL` in the database before reading it. Columns like `Email` and `Phone` are not marked `NOT NULL` in the schema, so this guard prevents a runtime exception when those fields are empty.

`ExecuteReader()` returns a `SqliteDataReader`, which works like a cursor. Each call to `reader.Read()` advances it to the next row and returns `false` when all rows are exhausted. `GetInt32(0)`, `GetString(1)`, etc. read column values by their zero-based column index matching the `SELECT` order.

---

## 6. Data Model

**File:** `Models/Employee.cs`

```csharp
public class Employee
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Department { get; set; } = "";
    public string Role { get; set; } = "";
    public string Status { get; set; } = "";
    public string Email { get; set; } = "";
    public string Phone { get; set; } = "";
    public string HireDate { get; set; } = "";
    public double Salary { get; set; }
    public string SalaryFormatted => Salary.ToString("C0");
}
```

`Employee` is a plain C# class (a POCO — Plain Old CLR Object). Its properties map one-to-one to the columns in the `Employees` database table.

`= ""` on the string properties are **default value initialisers**. Because `Nullable = enable` is set in the project, the compiler would warn that a string property might be `null` unless we either mark it nullable (`string?`) or give it a non-null default. The `= ""` is the cleaner choice here, since these fields always have database values.

`SalaryFormatted` is a **computed property** (read-only, no setter). It has no backing field; it calculates its value on demand by formatting the `Salary` double using the `"C0"` format specifier, which produces a locale-aware currency string with no decimal places (e.g., `$85,000` on a US system).

This property is used directly in the DataGrid XAML binding `{Binding SalaryFormatted}`, keeping the formatting logic in the model rather than in the UI.

---

## 7. Login Page

### LoginWindow.xaml — UI Layout

The login window is a fixed-size, non-resizable window (420×520 pixels) centred on screen. It has two layers of visual structure.

**Background gradient:**
```xml
<Window.Background>
    <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
        <GradientStop Color="#1B2A4A" Offset="0"/>  <!-- dark navy top-left -->
        <GradientStop Color="#2B5278" Offset="1"/>  <!-- lighter blue bottom-right -->
    </LinearGradientBrush>
</Window.Background>
```

`StartPoint="0,0"` is the top-left corner and `EndPoint="1,1"` is the bottom-right corner, creating a diagonal gradient. `Offset` values are fractions from 0.0 to 1.0 defining where along the gradient axis each colour lives.

**Card panel:**
```xml
<Border Background="White" CornerRadius="14" Width="340"
        VerticalAlignment="Center" Padding="36,32">
    <Border.Effect>
        <DropShadowEffect BlurRadius="30" ShadowDepth="8" Opacity="0.25"/>
    </Border.Effect>
    <StackPanel> ... </StackPanel>
</Border>
```

`Border` is WPF's general-purpose container that can have a background, rounded corners, and visual effects. `CornerRadius="14"` rounds all four corners. `VerticalAlignment="Center"` positions the card in the vertical centre of the window (which works because the parent `Grid` stretches to fill the window). The `DropShadowEffect` is a built-in WPF bitmap effect that renders a soft shadow behind the border, creating the elevated card appearance.

**Input fields:**

Native WPF `TextBox` and `PasswordBox` controls do not support `CornerRadius`. To work around this, each input is wrapped in a styled `Border` that provides the rounded corners and border colour, while the inner control itself has its own border set to zero thickness:

```xml
<Border BorderBrush="#D1D5DB" BorderThickness="1" CornerRadius="6" Background="#F9FAFB">
    <TextBox x:Name="UsernameBox" BorderThickness="0" Background="Transparent" .../>
</Border>
```

**Login button with custom template:**

WPF's default button has a platform-styled chrome that ignores `CornerRadius`. To make a rounded button, the entire visual template is replaced:

```xml
<Button.Style>
    <Style TargetType="Button">
        <Setter Property="Background" Value="#1B4F8A"/>
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="Button">
                    <Border Background="{TemplateBinding Background}" CornerRadius="7">
                        <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                    </Border>
                    <ControlTemplate.Triggers>
                        <Trigger Property="IsMouseOver" Value="True">
                            <Setter Property="Background" Value="#154080"/>
                        </Trigger>
                        <Trigger Property="IsPressed" Value="True">
                            <Setter Property="Background" Value="#0F3060"/>
                        </Trigger>
                    </ControlTemplate.Triggers>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
    </Style>
</Button.Style>
```

`{TemplateBinding Background}` is a special binding used inside control templates that reads the `Background` property from the button itself (set by the outer `<Setter>`). `ContentPresenter` is the placeholder that renders whatever is in the button's `Content` property (the text "Sign In"). The `ControlTemplate.Triggers` change the background colour when the mouse hovers or the button is pressed, providing visual feedback.

**Error border:**
```xml
<Border x:Name="ErrorBorder" Background="#FEF2F2" CornerRadius="6"
        Visibility="Collapsed">
    <TextBlock x:Name="ErrorText" Foreground="#DC2626" .../>
</Border>
```

`Visibility="Collapsed"` means the element takes up no space and is invisible by default. When an error occurs, the code-behind sets `ErrorBorder.Visibility = Visibility.Visible` to reveal the red error panel.

### LoginWindow.xaml.cs — Login Logic

```csharp
public LoginWindow()
{
    InitializeComponent();
    UsernameBox.Focus();
}
```

`InitializeComponent()` is generated automatically by the XAML compiler. It parses the `.xaml` file and creates all the UI objects, wires up event handlers, and makes named controls (like `UsernameBox`) available as fields. It must be the first call in the constructor.

`UsernameBox.Focus()` immediately places the keyboard cursor in the username field so the user can start typing without having to click first.

**AttemptLogin:**
```csharp
private void AttemptLogin()
{
    var username = UsernameBox.Text.Trim();
    var password = PasswordBox.Password;

    if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
    {
        ShowError("Please enter both username and password.");
        return;
    }

    if (!DatabaseHelper.ValidateLogin(username, password))
    {
        ShowError("Invalid username or password. Please try again.");
        PasswordBox.Clear();
        PasswordBox.Focus();
        return;
    }

    var searchWindow = new SearchWindow(username);
    searchWindow.Show();
    Close();
}
```

Note that `PasswordBox` exposes its content through the `.Password` property (not `.Text`). WPF deliberately keeps passwords in a separate, non-bindable property for security — it holds the value in a `SecureString` internally and does not allow data binding to it, reducing the risk of the password being copied into memory by the data binding engine.

`.Trim()` on the username removes accidental leading/trailing spaces (a common source of failed logins).

On success: the `SearchWindow` is instantiated with the username as a parameter (so the search page can display "Logged in as: admin"), shown with `.Show()`, and then the login window closes itself with `Close()`.

**Event routing:**
```csharp
private void LoginButton_Click(object sender, RoutedEventArgs e) => AttemptLogin();

private void Input_KeyDown(object sender, KeyEventArgs e)
{
    if (e.Key == Key.Enter) AttemptLogin();
}
```

Both the button click and pressing Enter in either input field call the same `AttemptLogin()` method. This is standard UX practice — users expect Enter to submit a form.

---

## 8. Search Page

### SearchWindow.xaml — Layout and Styles

The search window uses a four-row `Grid` to divide the screen into fixed-height zones:

```xml
<Grid.RowDefinitions>
    <RowDefinition Height="60"/>   <!-- Header bar -->
    <RowDefinition Height="Auto"/> <!-- Filter panel: grows to fit content -->
    <RowDefinition Height="*"/>    <!-- Results: takes all remaining space -->
    <RowDefinition Height="34"/>   <!-- Status bar -->
</Grid.RowDefinitions>
```

`Height="Auto"` means the row is exactly as tall as its content requires. `Height="*"` means the row takes all space left over after the fixed and auto rows have been measured. This makes the results grid expand to fill the window as the user resizes it.

**Window-scoped styles** are declared in `<Window.Resources>` and referenced by key:

```xml
<Style x:Key="FilterLabel" TargetType="TextBlock">
    <Setter Property="FontSize" Value="12"/>
    <Setter Property="FontWeight" Value="SemiBold"/>
    ...
</Style>
```

Any `TextBlock` in this window can then write `Style="{StaticResource FilterLabel}"` instead of repeating all four property values. This is the WPF equivalent of a CSS class. `StaticResource` means the style is looked up once at load time, which is more efficient than `DynamicResource` (which re-evaluates if the resource changes at runtime).

**DataGrid column definitions:**
```xml
<DataGrid x:Name="ResultsGrid"
          AutoGenerateColumns="False"
          IsReadOnly="True"
          AlternatingRowBackground="#FAFAFA"
          ...>
    <DataGrid.Columns>
        <DataGridTextColumn Header="Name" Binding="{Binding Name}" Width="*" MinWidth="120"/>
        <DataGridTextColumn Header="Department" Binding="{Binding Department}" Width="110"/>
        ...
    </DataGrid.Columns>
</DataGrid>
```

`AutoGenerateColumns="False"` disables WPF's default behaviour of auto-creating one column per property on the bound object. This gives full control over which columns appear and in what order.

`{Binding Name}` tells the DataGrid to read the `Name` property from each `Employee` object in the bound list. WPF uses reflection at runtime to find the property by name.

`Width="*"` on the Name and Email columns means they share the remaining width proportionally (like `*` rows in a Grid). Fixed-width columns (e.g., `Width="110"`) always occupy exactly that many pixels.

**Status badge — DataGridTemplateColumn:**

The Status column uses a `DataGridTemplateColumn` instead of a `DataGridTextColumn` because it needs custom visual rendering (a coloured pill badge), not just plain text:

```xml
<DataGridTemplateColumn Header="Status" Width="90">
    <DataGridTemplateColumn.CellTemplate>
        <DataTemplate>
            <Border CornerRadius="10" Padding="8,3" HorizontalAlignment="Left">
                <Border.Style>
                    <Style TargetType="Border">
                        <Setter Property="Background" Value="#E5E7EB"/>
                        <Style.Triggers>
                            <DataTrigger Binding="{Binding Status}" Value="Active">
                                <Setter Property="Background" Value="#D1FAE5"/>
                            </DataTrigger>
                            <DataTrigger Binding="{Binding Status}" Value="Inactive">
                                <Setter Property="Background" Value="#FEE2E2"/>
                            </DataTrigger>
                            <DataTrigger Binding="{Binding Status}" Value="On Leave">
                                <Setter Property="Background" Value="#FEF3C7"/>
                            </DataTrigger>
                        </Style.Triggers>
                    </Style>
                </Border.Style>
                <TextBlock .../>
            </Border>
        </DataTemplate>
    </DataGridTemplateColumn.CellTemplate>
</DataGridTemplateColumn>
```

`DataTrigger` is a style trigger that fires when a bound data value matches a specific string. The default setter (`#E5E7EB`, grey) applies when none of the triggers match. When `Status` is `"Active"`, the background becomes green (`#D1FAE5`); `"Inactive"` turns it red; `"On Leave"` turns it amber. The same `DataTrigger` pattern is applied to the `TextBlock` inside to also change the text colour to match.

**Filter panel layout:**

The filters are arranged in two rows using nested `Grid` elements. The first row has five columns (Name field, spacer, Department combo, spacer, Role combo):

```xml
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="*"/>    <!-- Name: fills remaining space -->
    <ColumnDefinition Width="14"/>   <!-- spacer -->
    <ColumnDefinition Width="160"/>  <!-- Department -->
    <ColumnDefinition Width="14"/>   <!-- spacer -->
    <ColumnDefinition Width="160"/>  <!-- Role -->
</Grid.ColumnDefinitions>
```

The `Width="14"` spacer columns replace `Margin` settings, making the gap between controls explicit and easy to adjust in one place.

### SearchWindow.xaml.cs — Search Logic

```csharp
public SearchWindow(string username)
{
    InitializeComponent();
    _username = username;
    UserLabel.Text = $"Logged in as: {username}";
    RunSearch();
}
```

The constructor accepts the logged-in `username` from `LoginWindow`. It calls `RunSearch()` immediately after setup, so the DataGrid shows all employees the moment the window opens, rather than showing a blank grid that requires the user to click Search first.

**RunSearch:**
```csharp
private void RunSearch()
{
    var name       = NameBox.Text.Trim();
    var department = (DepartmentCombo.SelectedItem as System.Windows.Controls.ComboBoxItem)
                         ?.Content?.ToString();
    var role       = (RoleCombo.SelectedItem as System.Windows.Controls.ComboBoxItem)
                         ?.Content?.ToString();
    var status     = (StatusCombo.SelectedItem as System.Windows.Controls.ComboBoxItem)
                         ?.Content?.ToString();

    var results = DatabaseHelper.SearchEmployees(name, department, role, status);
    ResultsGrid.ItemsSource = results;

    if (results.Count == 0)
    {
        EmptyState.Visibility = Visibility.Visible;
        ResultsGrid.Visibility = Visibility.Collapsed;
        StatusText.Text = "No employees match the selected filters.";
    }
    else
    {
        EmptyState.Visibility = Visibility.Collapsed;
        ResultsGrid.Visibility = Visibility.Visible;
        StatusText.Text = $"{results.Count} employee{(results.Count == 1 ? "" : "s")} found.";
    }
}
```

Reading the selected `ComboBox` value requires casting `SelectedItem` (which is typed as `object`) to `ComboBoxItem`, then reading `.Content`. The `?.` null-conditional operator is used at each step: if `SelectedItem` is `null` at any point, the whole expression short-circuits to `null` instead of throwing a `NullReferenceException`.

`ResultsGrid.ItemsSource = results` hands the `List<Employee>` to the DataGrid. WPF's data binding engine then iterates the list and creates one row per item, pulling property values through each column's `{Binding ...}` expression.

`(results.Count == 1 ? "" : "s")` is a ternary expression that correctly pluralises "employee" vs "employees" in the status bar.

**Empty state toggle:**
Rather than showing the DataGrid with no rows (which looks like a broken grid), the empty state panel (`EmptyState`) is toggled visible and the DataGrid is collapsed when there are no results. When results exist, the inverse applies. Both elements sit in the same `Grid.Row="1"` inside the results panel and overlap each other — at any time, only one is `Visible`.

**ClearButton:**
```csharp
private void ClearButton_Click(object sender, RoutedEventArgs e)
{
    NameBox.Clear();
    DepartmentCombo.SelectedIndex = 0;
    RoleCombo.SelectedIndex = 0;
    StatusCombo.SelectedIndex = 0;
    RunSearch();
}
```

`SelectedIndex = 0` selects the first item in each combo box, which is always the `"All"` option. Calling `RunSearch()` immediately after re-runs the query with no filters, showing all records.

**Logout:**
```csharp
private void LogoutButton_Click(object sender, RoutedEventArgs e)
{
    var login = new LoginWindow();
    login.Show();
    Close();
}
```

The reverse of login: a new `LoginWindow` is created and shown, then the current `SearchWindow` closes itself. This ensures the application always has exactly one visible window.

---

## 9. End-to-End Application Flow

```
dotnet run
    │
    ▼
App.OnStartup()
    │  DatabaseHelper.Initialize()
    │  ├─ Open/create employeesearch.db
    │  ├─ CREATE TABLE IF NOT EXISTS Users
    │  ├─ CREATE TABLE IF NOT EXISTS Employees
    │  ├─ SeedAdminUser()  → insert admin/admin123 if missing
    │  └─ SeedEmployees()  → insert 15 sample rows if missing
    │
    ▼
LoginWindow opens (StartupUri)
    │  User types username + password
    │  Clicks "Sign In" or presses Enter
    │
    ▼
LoginWindow.AttemptLogin()
    │  DatabaseHelper.ValidateLogin(username, password)
    │  ├─ SELECT PasswordHash WHERE Username = ?
    │  └─ BCrypt.Verify(plainText, hash)  → true/false
    │
    ├─ [FAIL] ShowError(), clear password field, stay on login
    │
    └─ [OK] new SearchWindow(username).Show()
            LoginWindow.Close()
                │
                ▼
            SearchWindow opens
                │  UserLabel shows "Logged in as: admin"
                │  RunSearch() called immediately (no filters)
                │  → all 15 employees loaded into DataGrid
                │
                │  User adjusts filters, clicks Search
                │
                ▼
            SearchWindow.RunSearch()
                │  Reads NameBox.Text, ComboBox selections
                │  DatabaseHelper.SearchEmployees(name, dept, role, status)
                │  ├─ Build dynamic WHERE clause
                │  ├─ Bind parameters
                │  ├─ Execute SELECT
                │  └─ Return List<Employee>
                │
                │  ResultsGrid.ItemsSource = results
                │  Update StatusText ("X employees found")
                │
                │  User clicks Logout
                ▼
            new LoginWindow().Show()
            SearchWindow.Close()
```

---

## 10. Security Design

### Passwords are never stored in plain text

The BCrypt algorithm is used for all password storage. When the admin account is seeded:

```
"admin123"  →  BCrypt.HashPassword()  →  "$2a$11$V3lF...randomhash..."
```

Only the hash is saved to the database. When a user logs in, BCrypt re-hashes the input and compares it to the stored hash — the original password cannot be recovered even if the database file is stolen.

BCrypt is deliberately slow (the `$11$` in the hash means 2^11 = 2048 iterations), which makes brute-force attacks computationally expensive.

### All queries use parameterized statements

No string concatenation is used to build SQL with user input. Every variable piece of data goes through `cmd.Parameters.AddWithValue("@param", value)`. This means the database driver handles escaping, so malicious input like:

```
username: admin' OR '1'='1
```

is treated as a literal string value, not as SQL syntax. SQL injection is structurally impossible with this pattern.

### Generic error messages

`ValidateLogin` returns a simple `bool`. The login window shows the same error message whether the username doesn't exist or the password is wrong. This is intentional — a message like "username not found" would allow an attacker to enumerate valid usernames by probing different values.

---

*Document generated for EmployeeSearch v1.0 — .NET 8 WPF / SQLite*

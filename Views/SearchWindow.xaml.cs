using System.Windows;
using System.Windows.Input;
using EmployeeSearch.Database;

namespace EmployeeSearch.Views;

public partial class SearchWindow : Window
{
    private readonly string _username;

    public SearchWindow(string username)
    {
        InitializeComponent();
        _username = username;
        UserLabel.Text = $"Logged in as: {username}";
        RunSearch(); // load all employees on open
    }

    private void SearchButton_Click(object sender, RoutedEventArgs e) => RunSearch();

    private void Filter_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter) RunSearch();
    }

    private void ClearButton_Click(object sender, RoutedEventArgs e)
    {
        NameBox.Clear();
        DepartmentCombo.SelectedIndex = 0;
        RoleCombo.SelectedIndex = 0;
        StatusCombo.SelectedIndex = 0;
        RunSearch();
    }

    private void LogoutButton_Click(object sender, RoutedEventArgs e)
    {
        var login = new LoginWindow();
        login.Show();
        Close();
    }

    private void RunSearch()
    {
        var name       = NameBox.Text.Trim();
        var department = (DepartmentCombo.SelectedItem as System.Windows.Controls.ComboBoxItem)?.Content?.ToString();
        var role       = (RoleCombo.SelectedItem as System.Windows.Controls.ComboBoxItem)?.Content?.ToString();
        var status     = (StatusCombo.SelectedItem as System.Windows.Controls.ComboBoxItem)?.Content?.ToString();

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
}

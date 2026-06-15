using System.Windows;
using System.Windows.Input;
using EmployeeSearch.Database;

namespace EmployeeSearch.Views;

public partial class LoginWindow : Window
{
    public LoginWindow()
    {
        InitializeComponent();
        UsernameBox.Focus();
    }

    private void LoginButton_Click(object sender, RoutedEventArgs e) => AttemptLogin();

    private void Input_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter) AttemptLogin();
    }

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

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        ErrorBorder.Visibility = Visibility.Visible;
    }
}

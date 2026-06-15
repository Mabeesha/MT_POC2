using System.Windows;
using EmployeeSearch.Database;

namespace EmployeeSearch;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        DatabaseHelper.Initialize();
    }
}

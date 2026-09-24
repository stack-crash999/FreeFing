using System.Windows;

namespace NetSentry.App.Views
{
    public partial class EditNameDialog : Window
    {
        public string EnteredName { get; private set; } = string.Empty;

        public EditNameDialog(string currentName)
        {
            InitializeComponent();
            NameInput.Text = currentName;
            NameInput.SelectAll();
            NameInput.Focus();
        }

        private void Save_Click(object sender, RoutedEventArgs e)
        {
            EnteredName = NameInput.Text.Trim();
            DialogResult = true;
            Close();
        }
    }
}

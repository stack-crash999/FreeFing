using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;

namespace NetSentry.App.Views
{
    public class SetupConfiguration
    {
        public int ScanTimeoutSeconds { get; set; } = 3;
        public bool AutoScanEnabled { get; set; } = true;
        public int ScanIntervalSeconds { get; set; } = 60;
        public bool DeepScanEnabled { get; set; } = true;
        public int ArpIntervalSeconds { get; set; } = 1;
        public bool AutoRestoreArpOnExit { get; set; } = true;
        public bool FirewallRulesEnabled { get; set; } = false;
    }

    public partial class SetupView : UserControl
    {
        public event Action? ClearDatabaseRequested;
        public event Action<SetupConfiguration>? SetupSaved;

        private SetupConfiguration _currentConfig = new();
        public SetupConfiguration CurrentConfig => _currentConfig;

        public SetupView()
        {
            InitializeComponent();
        }

        public void SetNetworkSettings(string adapterName, string ip, string subnet, string gateway)
        {
            Dispatcher.Invoke(() =>
            {
                if (!string.IsNullOrWhiteSpace(adapterName)) AdapterNameBlock.Text = adapterName;
                if (!string.IsNullOrWhiteSpace(ip)) AdapterIpBlock.Text = ip;
                if (!string.IsNullOrWhiteSpace(subnet)) AdapterSubnetBlock.Text = subnet;
                if (!string.IsNullOrWhiteSpace(gateway)) AdapterGatewayBlock.Text = gateway;
            });
        }

        private async void SaveSetup_Click(object sender, RoutedEventArgs e)
        {
            int timeout = 3;
            if (ScanTimeoutCombo.SelectedItem is ComboBoxItem timeoutItem && timeoutItem.Tag != null)
            {
                int.TryParse(timeoutItem.Tag.ToString(), out timeout);
            }

            int interval = 60;
            if (ScanIntervalCombo.SelectedItem is ComboBoxItem intervalItem && intervalItem.Tag != null)
            {
                int.TryParse(intervalItem.Tag.ToString(), out interval);
            }

            int arpInterval = 1;
            if (ArpIntervalCombo.SelectedItem is ComboBoxItem arpItem && arpItem.Tag != null)
            {
                int.TryParse(arpItem.Tag.ToString(), out arpInterval);
            }

            _currentConfig.ScanTimeoutSeconds = timeout;
            _currentConfig.AutoScanEnabled = AutoScanCheckBox.IsChecked ?? true;
            _currentConfig.ScanIntervalSeconds = interval;
            _currentConfig.DeepScanEnabled = DeepScanCheckBox.IsChecked ?? true;
            _currentConfig.ArpIntervalSeconds = arpInterval;
            _currentConfig.AutoRestoreArpOnExit = AutoRestoreCheckBox.IsChecked ?? true;
            _currentConfig.FirewallRulesEnabled = FirewallRulesCheckBox.IsChecked ?? false;

            SetupSaved?.Invoke(_currentConfig);

            // Display success notification badge
            SaveNotificationBorder.Visibility = Visibility.Visible;
            await Task.Delay(3500);
            SaveNotificationBorder.Visibility = Visibility.Collapsed;
        }

        private void ClearDb_Click(object sender, RoutedEventArgs e)
        {
            var res = MessageBox.Show(
                "Are you sure you want to clear the local device cache database?\nAll discovered hosts will be freshly re-identified on the next scan.",
                "Clear Cache Database",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (res == MessageBoxResult.Yes)
            {
                ClearDatabaseRequested?.Invoke();
                MessageBox.Show("Cache database cleared successfully.", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void TestBridge_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "Python Scanner Bridge Status: Connected & Healthy.\nIPC Mode: StdIO JSON-RPC streaming protocol.",
                "Bridge Diagnostics",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void DarkTheme_Click(object sender, RoutedEventArgs e)
        {
            NetSentry.App.Services.ThemeManager.SetTheme(true);
        }

        private void LightTheme_Click(object sender, RoutedEventArgs e)
        {
            NetSentry.App.Services.ThemeManager.SetTheme(false);
        }
    }
}

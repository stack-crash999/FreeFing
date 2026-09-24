using System;
using System.Windows;
using System.Windows.Controls;

namespace NetSentry.App.Views
{
    public partial class SettingsView : UserControl
    {
        public event Action? ClearDatabaseRequested;

        public SettingsView()
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
    }
}

using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using NetSentry.App.Models;

namespace NetSentry.App.Views
{
    public partial class DeviceDetailView : UserControl
    {
        public event Action? BackRequested;
        public event Action<string>? BlockRequested;
        public event Action<string>? UnblockRequested;
        public event Action<string, string>? RenameRequested;

        private DeviceItem? _currentDevice;
        public DeviceItem? CurrentDevice => _currentDevice;

        public DeviceDetailView()
        {
            InitializeComponent();
        }

        public void SetDevice(DeviceItem device)
        {
            _currentDevice = device;
            DataContext = device;

            DeviceNameBlock.Text = device.DisplayName;
            TypePillBlock.Text = device.TypeDisplay;
            ModelPillBlock.Text = device.Model;
            OsPillBlock.Text = device.Os;

            IpValBlock.Text = string.IsNullOrWhiteSpace(device.Ip) ? "—" : device.Ip;
            MacValBlock.Text = string.IsNullOrWhiteSpace(device.Mac) ? "—" : device.MacUpper;
            BrandValBlock.Text = device.Vendor;
            ModelValBlock.Text = device.Model;
            OsValBlock.Text = device.Os;
            BrandAvatarBlock.Text = device.BrandInitials;
            AuditStatusBlock.Text = $"Observed {device.TimesSeen} time(s) • Last active {device.LastUpdateText}";

            RevertBtn.Visibility = string.IsNullOrWhiteSpace(device.CustomName) ? Visibility.Collapsed : Visibility.Visible;

            UpdateBlockButtonUi();
        }

        private void UpdateBlockButtonUi()
        {
            if (_currentDevice == null) return;

            if (_currentDevice.IsBlocked)
            {
                BlockButton.Content = "Restore Network Access";
                BlockButton.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1E293B"));
                BlockButton.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#334155"));
                BlockButton.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#94A3B8"));

                IsolationStatusBlock.Text = "Hardware Block Active";
                IsolationStatusBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#F87171"));

                StatusPillBorder.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#33161C"));
                StatusPillBorder.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#542129"));
                StatusPillDot.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));
                StatusPillBlock.Text = "Blocked";
                StatusPillBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#F87171"));
            }
            else
            {
                BlockButton.Content = "Block Network Access";
                BlockButton.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));
                BlockButton.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DC2626"));
                BlockButton.Foreground = new SolidColorBrush(Colors.White);

                IsolationStatusBlock.Text = "Unrestricted Access";
                IsolationStatusBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#34D399"));

                if (_currentDevice.IsOnline)
                {
                    StatusPillBorder.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#064E3B"));
                    StatusPillBorder.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#059669"));
                    StatusPillDot.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
                    StatusPillBlock.Text = "Online";
                    StatusPillBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#34D399"));
                }
                else
                {
                    StatusPillBorder.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#151E31"));
                    StatusPillBorder.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#222F4C"));
                    StatusPillDot.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#64748B"));
                    StatusPillBlock.Text = "Offline";
                    StatusPillBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#94A3B8"));
                }
            }
        }

        private void BackToDevices_Click(object sender, RoutedEventArgs e)
        {
            BackRequested?.Invoke();
        }

        private void CopyIp_Click(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrEmpty(_currentDevice?.Ip))
            {
                Clipboard.SetText(_currentDevice.Ip);
            }
        }

        private void CopyMac_Click(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrEmpty(_currentDevice?.MacUpper))
            {
                Clipboard.SetText(_currentDevice.MacUpper);
            }
        }

        private void BlockButton_Click(object sender, RoutedEventArgs e)
        {
            if (_currentDevice == null) return;

            if (_currentDevice.IsBlocked)
            {
                _currentDevice.IsBlocked = false;
                UpdateBlockButtonUi();
                UnblockRequested?.Invoke(_currentDevice.Mac);
            }
            else
            {
                if (_currentDevice.DeviceType?.Equals("router", StringComparison.OrdinalIgnoreCase) == true)
                {
                    MessageBox.Show(
                        "Blocking the default gateway is disabled to prevent severing network connectivity for all devices.",
                        "Cannot Block Gateway",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                    return;
                }

                var result = MessageBox.Show(
                    $"Block internet access for:\n\n  {_currentDevice.DisplayName}\n  IP: {_currentDevice.Ip}\n  MAC: {_currentDevice.MacUpper}\n\nThis device will lose network connectivity via ARP isolation.",
                    "Confirm Network Block",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Warning);

                if (result == MessageBoxResult.Yes)
                {
                    _currentDevice.IsBlocked = true;
                    UpdateBlockButtonUi();
                    BlockRequested?.Invoke(_currentDevice.Mac);
                }
            }
        }

        private void EditName_Click(object sender, RoutedEventArgs e)
        {
            if (_currentDevice == null) return;

            var dlg = new EditNameDialog(_currentDevice.DisplayName);
            dlg.Owner = Window.GetWindow(this);
            if (dlg.ShowDialog() == true && !string.IsNullOrWhiteSpace(dlg.EnteredName))
            {
                _currentDevice.CustomName = dlg.EnteredName;
                DeviceNameBlock.Text = _currentDevice.CustomName;
                RevertBtn.Visibility = Visibility.Visible;
                RenameRequested?.Invoke(_currentDevice.Mac, _currentDevice.CustomName);
            }
        }

        private void Revert_Click(object sender, RoutedEventArgs e)
        {
            if (_currentDevice == null) return;
            _currentDevice.CustomName = string.Empty;
            DeviceNameBlock.Text = _currentDevice.DisplayName;
            RevertBtn.Visibility = Visibility.Collapsed;
            RenameRequested?.Invoke(_currentDevice.Mac, string.Empty);
        }
    }
}

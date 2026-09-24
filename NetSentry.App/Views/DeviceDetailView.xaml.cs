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
            device.EnsureDefaultPortsAndLink();

            // Header titles
            DeviceNameBlock.Text = device.DisplayName;
            DeviceSubtitleBlock.Text = $"{device.Vendor} • IP: {device.Ip} • MAC: {device.MacUpper}";

            // Prominent Model Identification Banner
            ProminentModelBlock.Text = device.Model;
            ProminentVendorBlock.Text = $"Manufacturer: {device.Vendor} • Device class: {device.TypeDisplay} • Detected via OUI & broadcast fingerprints";
            DeviceIconGlyphBlock.Text = device.IconGlyph;

            // Badges
            TypePillBlock.Text = $"Category: {device.TypeDisplay}";
            OsPillBlock.Text = $"OS: {device.Os}";
            LatencyPillBlock.Text = $"Latency: {device.LatencyDisplay}";

            // Specification Values
            IpValBlock.Text = string.IsNullOrWhiteSpace(device.Ip) ? "—" : device.Ip;
            MacValBlock.Text = string.IsNullOrWhiteSpace(device.Mac) ? "—" : device.MacUpper;
            BrandValBlock.Text = device.Vendor;
            ModelValBlock.Text = device.Model;
            OsValBlock.Text = device.Os;
            HostnameValBlock.Text = string.IsNullOrWhiteSpace(device.Hostname) ? (string.IsNullOrWhiteSpace(device.Ip) ? "—" : $"host-{device.Ip.Replace('.', '-')}.lan") : device.Hostname;
            BrandAvatarBlock.Text = device.BrandInitials;
            AuditStatusBlock.Text = $"Observed {device.TimesSeen} time(s) • Last active {device.LastUpdateText}";

            // Link & Telemetry
            MediumValBlock.Text = device.PhysicalLinkSummary;
            SpeedValBlock.Text = device.LinkSpeedDisplay;
            LatencyValBlock.Text = $"{device.LatencyDisplay} (ICMP Round-Trip)";
            SignalProgressBar.Value = Math.Clamp(device.SignalQualityPercent, 10, 100);
            SignalValBlock.Text = $"{device.SignalQualityPercent}% ({(device.SignalQualityPercent >= 75 ? "Excellent" : (device.SignalQualityPercent >= 50 ? "Good" : "Fair"))})";

            // Open Ports
            PortsItemsControl.ItemsSource = device.OpenPorts;
            PortsSummaryBlock.Text = $"{device.OpenPorts.Count} Port(s) Active";
            bool hasRisk = false;
            foreach (var p in device.OpenPorts)
            {
                if (p.IsSecurityRisk) hasRisk = true;
            }
            VulnerablePortsBlock.Text = hasRisk ? "ALERT / RISK" : "SECURE";
            VulnerablePortsBlock.Foreground = hasRisk 
                ? new SolidColorBrush(Color.FromRgb(0xEF, 0x44, 0x44)) 
                : new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81));

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
                IsolationDescBlock.Text = "Host ARP requests are poisoned. All router and external network traffic is disconnected.";

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
                IsolationStatusBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
                IsolationDescBlock.Text = "Host has standard bidirectional gateway routing on the local subnet.";

                if (_currentDevice.IsOnline)
                {
                    StatusPillBorder.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1A10B981"));
                    StatusPillBorder.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
                    StatusPillDot.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
                    StatusPillBlock.Text = "Online";
                    StatusPillBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
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
                    $"Block internet access for:\n\n  {_currentDevice.DisplayName}\n  Model: {_currentDevice.Model}\n  IP: {_currentDevice.Ip}\n  MAC: {_currentDevice.MacUpper}\n\nThis device will lose network connectivity via ARP isolation.",
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
                DeviceNameBlock.Text = _currentDevice.DisplayName;
                RevertBtn.Visibility = Visibility.Visible;
                RenameRequested?.Invoke(_currentDevice.Mac, dlg.EnteredName);
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

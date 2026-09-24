using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using NetSentry.App.Models;
using NetSentry.App.Services;

namespace NetSentry.App
{
    public partial class MainWindow : Window
    {
        private readonly PythonBridge _bridge = new();
        private readonly ObservableCollection<DeviceItem> _devices = new();
        private bool _isScanning = false;
        private string _currentSubnet = "";
        private System.Windows.Threading.DispatcherTimer? _telemetryTimer;

        public MainWindow()
        {
            InitializeComponent();
            DevicesListView.ItemsSource = _devices;

            // Python Bridge Events
            _bridge.DeviceFound += OnDeviceFound;
            _bridge.DeviceUpdated += OnDeviceUpdated;
            _bridge.ScanProgress += OnScanProgress;
            _bridge.ScanComplete += OnScanComplete;
            _bridge.NetworkUpdated += OnNetworkUpdated;
            _bridge.DevicesCleared += OnDevicesCleared;

            // System Network Change detection (Ethernet / Wi-Fi change)
            System.Net.NetworkInformation.NetworkChange.NetworkAddressChanged += async (_, _) =>
            {
                await Dispatcher.InvokeAsync(async () => await RefreshNetworkInfoAsync());
            };
        }

        private async void Window_Loaded(object sender, RoutedEventArgs e)
        {
            try
            {
                // Start Python bridge
                _bridge.Start();

                // Initial network info fetch
                await RefreshNetworkInfoAsync();

                // Fetch initial devices
                var initialDevices = await _bridge.GetDevicesAsync();
                _devices.Clear();
                foreach (var d in initialDevices)
                {
                    d.EnsureDefaultPortsAndLink();
                    _devices.Add(d);
                }

                UpdateHudStats();

                // Start live telemetry polling timer (every 6 seconds)
                _telemetryTimer = new System.Windows.Threading.DispatcherTimer
                {
                    Interval = TimeSpan.FromSeconds(6)
                };
                _telemetryTimer.Tick += async (_, _) => await RefreshNetworkInfoAsync();
                _telemetryTimer.Start();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error during Window_Loaded: {ex.Message}");
            }
        }

        private async Task RefreshNetworkInfoAsync()
        {
            try
            {
                var info = await _bridge.SendCommandAsync("get_info");
                if (info != null && info["network"] != null)
                {
                    ApplyNetworkInfo(info["network"]);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error refreshing network info: {ex.Message}");
            }
        }

        private void OnNetworkUpdated(System.Text.Json.Nodes.JsonNode? net)
        {
            Dispatcher.Invoke(() =>
            {
                ApplyNetworkInfo(net);
            });
        }

        private void OnDevicesCleared()
        {
            Dispatcher.Invoke(() =>
            {
                _devices.Clear();
                UpdateHudStats();
            });
        }

        private void ApplyNetworkInfo(System.Text.Json.Nodes.JsonNode? net)
        {
            if (net == null) return;
            string ssid = net["ssid"]?.GetValue<string>() ?? "Home";
            string subnet = net["subnet"]?.GetValue<string>() ?? "192.168.1.0/24";

            SubnetSubtitleBlock.Text = $"Connected to {ssid} Subnet • {subnet}";

            if (!string.IsNullOrEmpty(subnet))
            {
                if (!string.Equals(_currentSubnet, subnet, StringComparison.OrdinalIgnoreCase))
                {
                    _currentSubnet = subnet;
                    if (IPNetwork.TryParse(_currentSubnet, out var netObj))
                    {
                        var foreign = _devices.Where(d => IPAddress.TryParse(d.Ip, out var ipAddr) && !netObj.Contains(ipAddr)).ToList();
                        foreach (var f in foreign)
                        {
                            _devices.Remove(f);
                        }
                    }
                }
            }

            UpdateHudStats();
        }

        private void UpdateHudStats()
        {
            int total = _devices.Count;
            int online = _devices.Count(d => d.IsOnline && !d.IsBlocked);
            int blocked = _devices.Count(d => d.IsBlocked);

            TotalDevicesBlock.Text = total.ToString();
            OnlineStatusBlock.Text = $"{online} Active";
            BlockedStatusBlock.Text = $"{blocked} Devices";
            SecurityHealthBlock.Text = blocked > 0 ? "Defended" : "Optimal";
        }

        private void OnDeviceFound(DeviceItem dev)
        {
            Dispatcher.Invoke(() =>
            {
                if (!string.IsNullOrEmpty(_currentSubnet) && IPNetwork.TryParse(_currentSubnet, out var netObj))
                {
                    if (IPAddress.TryParse(dev.Ip, out var ipAddr) && !netObj.Contains(ipAddr))
                    {
                        return; // Discard host from foreign subnet
                    }
                }

                dev.EnsureDefaultPortsAndLink();
                var existing = _devices.FirstOrDefault(d => d.Mac.Equals(dev.Mac, StringComparison.OrdinalIgnoreCase));
                if (existing != null)
                {
                    existing.Ip = dev.Ip;
                    existing.Hostname = dev.Hostname;
                    existing.Model = dev.Model;
                    existing.Vendor = dev.Vendor;
                    existing.DeviceType = dev.DeviceType;
                    existing.IsOnline = dev.IsOnline;
                    existing.LastSeen = dev.LastSeen;
                    existing.TimesSeen = dev.TimesSeen;
                }
                else
                {
                    _devices.Add(dev);
                }
                UpdateHudStats();
            });
        }

        private void OnDeviceUpdated(DeviceItem dev)
        {
            Dispatcher.Invoke(() =>
            {
                if (!string.IsNullOrEmpty(_currentSubnet) && IPNetwork.TryParse(_currentSubnet, out var netObj))
                {
                    if (IPAddress.TryParse(dev.Ip, out var ipAddr) && !netObj.Contains(ipAddr))
                    {
                        return; // Discard host from foreign subnet
                    }
                }

                dev.EnsureDefaultPortsAndLink();
                var existing = _devices.FirstOrDefault(d => d.Mac.Equals(dev.Mac, StringComparison.OrdinalIgnoreCase));
                if (existing != null)
                {
                    existing.Ip = dev.Ip;
                    existing.Hostname = dev.Hostname;
                    existing.Model = dev.Model;
                    existing.Vendor = dev.Vendor;
                    existing.DeviceType = dev.DeviceType;
                    existing.IsOnline = dev.IsOnline;
                    existing.LastSeen = dev.LastSeen;
                    existing.TimesSeen = dev.TimesSeen;
                }
                UpdateHudStats();
            });
        }

        private void OnScanProgress(int percent)
        {
            Dispatcher.Invoke(() =>
            {
                if (_isScanning)
                {
                    ScanBtn.Content = $"Scanning ({percent}%)...";
                }
            });
        }

        private void OnScanComplete(int count)
        {
            Dispatcher.Invoke(() =>
            {
                _isScanning = false;
                ScanBtn.Content = "Scan Network";
                UpdateHudStats();
            });
        }

        private async void ScanBtn_Click(object sender, RoutedEventArgs e)
        {
            if (_isScanning)
            {
                _isScanning = false;
                ScanBtn.Content = "Scan Network";
                await _bridge.StopScanAsync();
            }
            else
            {
                _isScanning = true;
                ScanBtn.Content = "Scanning...";
                await RefreshNetworkInfoAsync();
                await _bridge.StartScanAsync();
            }
        }

        private async void ActionButton_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.DataContext is DeviceItem device)
            {
                if (device.IsBlocked)
                {
                    device.IsBlocked = false;
                    await _bridge.UnblockDeviceAsync(device.Mac);
                }
                else
                {
                    if (device.DeviceType?.Equals("router", StringComparison.OrdinalIgnoreCase) == true)
                    {
                        MessageBox.Show(
                            "Blocking the default gateway is disabled to prevent disconnecting all devices.",
                            "Cannot Block Gateway",
                            MessageBoxButton.OK,
                            MessageBoxImage.Warning);
                        return;
                    }

                    device.IsBlocked = true;
                    await _bridge.BlockDeviceAsync(device.Mac);
                }

                // Force refresh on bindings
                int idx = _devices.IndexOf(device);
                if (idx >= 0)
                {
                    _devices[idx] = device;
                }

                UpdateHudStats();
            }
        }

        private void NavDashboard_Click(object sender, RoutedEventArgs e)
        {
            DevicesListView.ScrollIntoView(_devices.FirstOrDefault());
        }

        private void NavDeviceMap_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                $"Device Topology Map:\n\n• Subnet: {_currentSubnet}\n• Monitored Nodes: {_devices.Count}\n• Active Gateways: 1",
                "Device Map",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void NavSecurity_Click(object sender, RoutedEventArgs e)
        {
            int blockedCount = _devices.Count(d => d.IsBlocked);
            MessageBox.Show(
                $"Security & Firewall Status:\n\n• ARP Spoof Isolation: Active\n• Blocked Devices: {blockedCount}\n• Subnet Enforcement: Enforced",
                "Security Status",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void NavSettings_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "NetGuardian Settings:\n\n• Theme: Fing Enterprise Navy / Blue\n• Subnet Filtering: Strict active subnet\n• Scan Engine: Native ARP + UPnP discovery",
                "Settings",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            _bridge.Dispose();
        }
    }
}
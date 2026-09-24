using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
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
        private string _currentSsid = "Home";
        private string _currentGatewayIp = "";
        private string _currentGatewayMac = "";
        private string _currentLocalIp = "";
        private string _currentPublicIp = "";
        private string _currentIsp = "";
        private System.Windows.Threading.DispatcherTimer? _telemetryTimer;

        // Visual Colors for Active/Inactive Tabs
        private readonly Brush _brushActiveBg = new SolidColorBrush(Color.FromRgb(0x25, 0x63, 0xEB));
        private readonly Brush _brushActiveFg = new SolidColorBrush(Colors.White);
        private readonly Brush _brushInactiveBg = new SolidColorBrush(Color.FromRgb(0x18, 0x20, 0x30));
        private readonly Brush _brushInactiveFg = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8));
        private readonly Brush _brushRailActiveBg = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B));
        private readonly Brush _brushRailActiveFg = new SolidColorBrush(Color.FromRgb(0x38, 0xBD, 0xF8));
        private readonly Brush _brushRailInactiveFg = new SolidColorBrush(Color.FromRgb(0x64, 0x74, 0x8B));

        public MainWindow()
        {
            InitializeComponent();

            // Wire Sub-View Events
            WireOverviewEvents();
            WireDeviceListEvents();
            WireDeviceDetailEvents();
            WireSecurityEvents();
            WireSetupEvents();

            // Python Bridge Events
            _bridge.DeviceFound += OnDeviceFound;
            _bridge.DeviceUpdated += OnDeviceUpdated;
            _bridge.ScanProgress += OnScanProgress;
            _bridge.ScanComplete += OnScanComplete;
            _bridge.NetworkUpdated += OnNetworkUpdated;
            _bridge.DevicesCleared += OnDevicesCleared;

            // System Network Change detection (Ethernet / Wi-Fi switch)
            System.Net.NetworkInformation.NetworkChange.NetworkAddressChanged += async (_, _) =>
            {
                await Dispatcher.InvokeAsync(async () => await RefreshNetworkInfoAsync());
            };
        }

        private void WireOverviewEvents()
        {
            OverviewControl.ScanRequested += async () => await StartScanAsync();
            OverviewControl.StopScanRequested += async () => await StopScanAsync();
            OverviewControl.NavigateToDevicesRequested += () => ShowTab("Devices");
        }

        private void WireDeviceListEvents()
        {
            DeviceListControl.DeviceSelected += (device) =>
            {
                DeviceDetailControl.SetDevice(device);
                ShowView(DeviceDetailControl);
            };

            DeviceListControl.BlockRequested += async (mac) => await BlockDeviceAsync(mac);
            DeviceListControl.UnblockRequested += async (mac) => await UnblockDeviceAsync(mac);
        }

        private void WireDeviceDetailEvents()
        {
            DeviceDetailControl.BackRequested += () =>
            {
                ShowTab("Devices");
            };

            DeviceDetailControl.BlockRequested += async (mac) => await BlockDeviceAsync(mac);
            DeviceDetailControl.UnblockRequested += async (mac) => await UnblockDeviceAsync(mac);
            DeviceDetailControl.RenameRequested += async (mac, name) =>
            {
                await _bridge.RenameDeviceAsync(mac, name);
                OverviewControl.AppendLog($"[DEVICE] Renamed device {mac} to '{name}'");
            };
        }

        private void WireSecurityEvents()
        {
            SecurityControl.UnblockRequested += async (mac) => await UnblockDeviceAsync(mac);
        }

        private void WireSetupEvents()
        {
            SetupControl.ClearDatabaseRequested += async () =>
            {
                await _bridge.SendCommandAsync("clear_devices");
                _devices.Clear();
                DeviceListControl.SetDevices(_devices);
                UpdateSubviewsHud();
                OverviewControl.AppendLog("[DATABASE] Cache database purged by user request.");
            };

            SetupControl.SetupSaved += (cfg) =>
            {
                if (_telemetryTimer != null)
                {
                    _telemetryTimer.Interval = TimeSpan.FromSeconds(Math.Max(5, cfg.ScanIntervalSeconds));
                }
                OverviewControl.AppendLog($"[SETUP] Configuration applied: Interval={cfg.ScanIntervalSeconds}s, Timeout={cfg.ScanTimeoutSeconds}s, DeepScan={cfg.DeepScanEnabled}, ARP={cfg.ArpIntervalSeconds}s");
            };
        }

        private async void Window_Loaded(object sender, RoutedEventArgs e)
        {
            try
            {
                ShowTab("Overview");

                // Start Python bridge
                _bridge.Start();

                // Initial network info fetch
                await RefreshNetworkInfoAsync();

                // Fetch initial devices from cache
                var initialDevices = await _bridge.GetDevicesAsync();
                _devices.Clear();
                foreach (var d in initialDevices)
                {
                    d.EnsureDefaultPortsAndLink();
                    _devices.Add(d);
                }

                DeviceListControl.SetDevices(_devices);
                SecurityControl.UpdateDevices(_devices);
                UpdateSubviewsHud();

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

        #region Multi-Page Navigation Logic

        private void ShowView(UIElement activeView)
        {
            OverviewControl.Visibility = (activeView == OverviewControl) ? Visibility.Visible : Visibility.Collapsed;
            DeviceListControl.Visibility = (activeView == DeviceListControl) ? Visibility.Visible : Visibility.Collapsed;
            DeviceDetailControl.Visibility = (activeView == DeviceDetailControl) ? Visibility.Visible : Visibility.Collapsed;
            SecurityControl.Visibility = (activeView == SecurityControl) ? Visibility.Visible : Visibility.Collapsed;
            SetupControl.Visibility = (activeView == SetupControl) ? Visibility.Visible : Visibility.Collapsed;
        }

        private void ShowTab(string tabName)
        {
            // Reset tab button styles
            ResetNavTabVisuals();

            switch (tabName)
            {
                case "Overview":
                    ShowView(OverviewControl);
                    HighlightNav(NavOverviewBtn, TopTabOverview);
                    break;

                case "Devices":
                    DeviceListControl.SetDevices(_devices);
                    ShowView(DeviceListControl);
                    HighlightNav(NavDevicesBtn, TopTabDevices);
                    break;

                case "Security":
                    SecurityControl.UpdateDevices(_devices);
                    ShowView(SecurityControl);
                    HighlightNav(NavSecurityBtn, TopTabSecurity);
                    break;

                case "Setup":
                    SetupControl.SetNetworkSettings("Primary Adapter", _currentLocalIp, _currentSubnet, _currentGatewayIp);
                    ShowView(SetupControl);
                    HighlightNav(NavSetupBtn, TopTabSetup);
                    break;
            }
        }

        private void ResetNavTabVisuals()
        {
            Button[] railButtons = { NavOverviewBtn, NavDevicesBtn, NavSecurityBtn, NavSetupBtn };
            foreach (var b in railButtons)
            {
                if (b != null)
                {
                    b.Background = Brushes.Transparent;
                    b.Foreground = _brushRailInactiveFg;
                }
            }

            Button[] topButtons = { TopTabOverview, TopTabDevices, TopTabSecurity, TopTabSetup };
            foreach (var b in topButtons)
            {
                if (b != null)
                {
                    b.Background = _brushInactiveBg;
                    b.Foreground = _brushInactiveFg;
                }
            }
        }

        private void HighlightNav(Button railBtn, Button topBtn)
        {
            if (railBtn != null)
            {
                railBtn.Background = _brushRailActiveBg;
                railBtn.Foreground = _brushRailActiveFg;
            }

            if (topBtn != null)
            {
                topBtn.Background = _brushActiveBg;
                topBtn.Foreground = _brushActiveFg;
            }
        }

        private void NavOverview_Click(object sender, RoutedEventArgs e) => ShowTab("Overview");
        private void NavDevices_Click(object sender, RoutedEventArgs e) => ShowTab("Devices");
        private void NavSecurity_Click(object sender, RoutedEventArgs e) => ShowTab("Security");
        private void NavSetup_Click(object sender, RoutedEventArgs e) => ShowTab("Setup");

        #endregion

        #region Scanning and Blocking Logic

        private async Task StartScanAsync()
        {
            if (_isScanning) return;
            _isScanning = true;

            GlobalScanBtn.Content = "Scanning...";
            OverviewControl.SetScanningState(true);
            OverviewControl.AppendLog("[SCAN] Subnet discovery sweep started...");

            await RefreshNetworkInfoAsync();
            await _bridge.StartScanAsync();
        }

        private async Task StopScanAsync()
        {
            _isScanning = false;
            GlobalScanBtn.Content = "Scan Network";
            OverviewControl.SetScanningState(false);
            OverviewControl.AppendLog("[SCAN] Scan cancelled by user.");

            await _bridge.StopScanAsync();
        }

        private async void GlobalScanBtn_Click(object sender, RoutedEventArgs e)
        {
            if (_isScanning)
            {
                await StopScanAsync();
            }
            else
            {
                await StartScanAsync();
            }
        }

        private async Task BlockDeviceAsync(string mac)
        {
            var dev = _devices.FirstOrDefault(d => d.Mac.Equals(mac, StringComparison.OrdinalIgnoreCase));
            if (dev != null)
            {
                dev.IsBlocked = true;
            }

            await _bridge.BlockDeviceAsync(mac);
            OverviewControl.AppendLog($"[DEFENSE] Hardware block enforced on target MAC {mac.ToUpperInvariant()} via ARP redirection.");
            SecurityControl.UpdateDevices(_devices);
            UpdateSubviewsHud();
        }

        private async Task UnblockDeviceAsync(string mac)
        {
            var dev = _devices.FirstOrDefault(d => d.Mac.Equals(mac, StringComparison.OrdinalIgnoreCase));
            if (dev != null)
            {
                dev.IsBlocked = false;
            }

            await _bridge.UnblockDeviceAsync(mac);
            OverviewControl.AppendLog($"[DEFENSE] Restored network routing for target MAC {mac.ToUpperInvariant()}.");
            SecurityControl.UpdateDevices(_devices);
            UpdateSubviewsHud();
        }

        #endregion

        #region Network & Device Events Handling

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
            Dispatcher.Invoke(() => ApplyNetworkInfo(net));
        }

        private void OnDevicesCleared()
        {
            Dispatcher.Invoke(() =>
            {
                _devices.Clear();
                DeviceListControl.SetDevices(_devices);
                SecurityControl.UpdateDevices(_devices);
                UpdateSubviewsHud();
            });
        }

        private void ApplyNetworkInfo(System.Text.Json.Nodes.JsonNode? net)
        {
            if (net == null) return;
            string ssid = net["ssid"]?.GetValue<string>() ?? "Home";
            string subnet = net["subnet"]?.GetValue<string>() ?? "192.168.1.0/24";
            string gateway = net["gateway"]?.GetValue<string>() ?? "192.168.1.1";
            string localIp = net["local_ip"]?.GetValue<string>() ?? "192.168.1.100";
            string publicIp = net["public_ip"]?.GetValue<string>() ?? "Resolving...";
            string isp = net["isp"]?.GetValue<string>() ?? "AT&T";

            string gatewayMac = net["gateway_mac"]?.GetValue<string>() ?? "";
            if (string.IsNullOrEmpty(gatewayMac))
            {
                var gwDevice = _devices.FirstOrDefault(d => d.Ip == gateway || d.DeviceType?.Equals("router", StringComparison.OrdinalIgnoreCase) == true);
                if (gwDevice != null) gatewayMac = gwDevice.MacUpper;
            }

            _currentSsid = ssid;
            _currentGatewayIp = gateway;
            _currentGatewayMac = gatewayMac;
            _currentLocalIp = localIp;
            _currentPublicIp = publicIp;
            _currentIsp = isp;

            TopSubnetBlock.Text = $"Connected to {ssid} Subnet • {subnet}";

            // Subnet switching isolation: purge any hosts from a different subnet
            if (!string.IsNullOrEmpty(subnet) && !string.Equals(_currentSubnet, subnet, StringComparison.OrdinalIgnoreCase))
            {
                _currentSubnet = subnet;
                OverviewControl.AppendLog($"[NETWORK] Subnet migration detected: Bound to {_currentSubnet}");

                if (IPNetwork.TryParse(_currentSubnet, out var netObj))
                {
                    var foreign = _devices.Where(d => IPAddress.TryParse(d.Ip, out var ipAddr) && !netObj.Contains(ipAddr)).ToList();
                    foreach (var f in foreign)
                    {
                        _devices.Remove(f);
                    }
                    DeviceListControl.SetDevices(_devices);
                }
            }

            // Forward telemetry to pages
            OverviewControl.SetNetworkInfo(ssid, localIp, subnet, gateway, string.IsNullOrEmpty(_currentGatewayMac) ? "--" : _currentGatewayMac, publicIp, isp, 7.8);
            DeviceListControl.SetNetworkName(ssid);
            SecurityControl.SetGatewayInfo(gateway);
            SetupControl.SetNetworkSettings("Default Adapter", localIp, subnet, gateway);

            UpdateSubviewsHud();
        }

        private void UpdateSubviewsHud()
        {
            int online = _devices.Count(d => d.IsOnline && !d.IsBlocked);
            int blocked = _devices.Count(d => d.IsBlocked);

            OverviewControl.SetDeviceCounts(online, blocked);
            SecurityControl.UpdateDevices(_devices);
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
                    OverviewControl.AppendLog($"[DISCOVERY] New node identified: {dev.DisplayName} ({dev.Ip}) - Model: {dev.Model}");
                }

                DeviceListControl.AddOrUpdateDevice(dev);

                // If currently inspecting this device, update detail view
                if (DeviceDetailControl.Visibility == Visibility.Visible &&
                    DeviceDetailControl.CurrentDevice?.Mac.Equals(dev.Mac, StringComparison.OrdinalIgnoreCase) == true)
                {
                    DeviceDetailControl.SetDevice(existing ?? dev);
                }

                UpdateSubviewsHud();
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
                        return;
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

                DeviceListControl.AddOrUpdateDevice(dev);

                if (DeviceDetailControl.Visibility == Visibility.Visible &&
                    DeviceDetailControl.CurrentDevice?.Mac.Equals(dev.Mac, StringComparison.OrdinalIgnoreCase) == true)
                {
                    DeviceDetailControl.SetDevice(existing ?? dev);
                }

                UpdateSubviewsHud();
            });
        }

        private void OnScanProgress(int percent)
        {
            Dispatcher.Invoke(() =>
            {
                if (_isScanning)
                {
                    GlobalScanBtn.Content = $"Scanning ({percent}%)...";
                    OverviewControl.SetScanProgress(percent);
                }
            });
        }

        private void OnScanComplete(int count)
        {
            Dispatcher.Invoke(() =>
            {
                _isScanning = false;
                GlobalScanBtn.Content = "Scan Network";
                OverviewControl.SetScanningState(false);
                OverviewControl.AppendLog($"[SCAN] Sweep completed. Discovered {count} responsive hosts.");
                UpdateSubviewsHud();
            });
        }

        #endregion

        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            _bridge.Dispose();
        }
    }
}
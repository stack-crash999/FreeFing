using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using System.Windows;
using NetSentry.App.Models;
using NetSentry.App.Services;

namespace NetSentry.App
{
    public partial class MainWindow : Window
    {
        private readonly PythonBridge _bridge = new();
        private readonly List<string> _navHistory = new();
        private int _historyIndex = -1;
        private bool _isScanning = false;
        private readonly List<DeviceItem> _deviceCache = new();
        private string _currentSubnet = "";
        private System.Windows.Threading.DispatcherTimer? _telemetryTimer;

        public MainWindow()
        {
            InitializeComponent();

            // View Events
            DeviceListControl.DeviceSelected += OnDeviceSelected;
            DeviceListControl.BlockRequested += OnBlockRequested;
            DeviceListControl.UnblockRequested += OnUnblockRequested;
            DeviceDetailControl.BlockRequested += OnBlockRequested;
            DeviceDetailControl.UnblockRequested += OnUnblockRequested;
            DeviceDetailControl.RenameRequested += OnRenameRequested;
            DeviceDetailControl.BackRequested += () => NavigateTo("devices", pushHistory: true);

            OverviewControl.ScanRequested += async () => await TriggerScanAsync();
            OverviewControl.StopScanRequested += async () => await TriggerStopScanAsync();
            OverviewControl.NavigateToDevicesRequested += () => NavigateTo("devices", pushHistory: true);

            // Python Bridge Events
            _bridge.DeviceFound += OnDeviceFound;
            _bridge.DeviceUpdated += OnDeviceUpdated;
            _bridge.ScanProgress += OnScanProgress;
            _bridge.ScanComplete += OnScanComplete;
            _bridge.ScanLog += OnScanLog;
            _bridge.NetworkUpdated += OnNetworkUpdated;
            _bridge.DevicesCleared += OnDevicesCleared;

            // System Network Change detection (Ethernet / Wi-Fi change)
            System.Net.NetworkInformation.NetworkChange.NetworkAddressChanged += async (_, _) =>
            {
                await Dispatcher.InvokeAsync(async () => await RefreshNetworkInfoAsync());
            };
        }

        private void LogDebug(string msg)
        {
            try
            {
                string logDir = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "NetSentry");
                System.IO.File.AppendAllText(System.IO.Path.Combine(logDir, "app_debug.log"), $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}] [MainWindow] {msg}\n");
            }
            catch { }
        }

        private async void Window_Loaded(object sender, RoutedEventArgs e)
        {
            try
            {
                LogDebug("Window_Loaded started.");
                NavigateTo("overview", pushHistory: true);

                // Start Python bridge
                LogDebug("Starting Python bridge...");
                _bridge.Start();
                LogDebug("Python bridge started.");

                // Initial network info fetch
                LogDebug("Refreshing network info...");
                await RefreshNetworkInfoAsync();
                LogDebug("Network info refreshed.");

                // Fetch initial devices
                LogDebug("Fetching initial devices...");
                var devices = await _bridge.GetDevicesAsync();
                LogDebug($"Fetched {devices.Count} initial devices.");
                _deviceCache.Clear();
                _deviceCache.AddRange(devices);
                LogDebug("Calling UpdateDeviceViews...");
                UpdateDeviceViews();
                LogDebug("UpdateDeviceViews finished successfully.");

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
                _deviceCache.Clear();
                UpdateDeviceViews();
                OverviewControl.AppendLog("[NETWORK] Active network switch detected. Prior subnet devices flushed.");
            });
        }

        private void ApplyNetworkInfo(System.Text.Json.Nodes.JsonNode? net)
        {
            if (net == null) return;
            string ssid = net["ssid"]?.GetValue<string>() ?? "Local Network";
            string subnet = net["subnet"]?.GetValue<string>() ?? "";
            string localIp = net["local_ip"]?.GetValue<string>() ?? "";
            string gatewayIp = net["gateway_ip"]?.GetValue<string>() ?? "";
            string gatewayMac = net["gateway_mac"]?.GetValue<string>() ?? "";
            string publicIp = net["public_ip"]?.GetValue<string>() ?? "";
            string isp = net["isp"]?.GetValue<string>() ?? "";
            double pingMs = 14.0;
            if (net["ping_ms"] != null)
            {
                pingMs = net["ping_ms"]!.GetValue<double>();
            }

            // Live update all UI elements
            SidebarNetName.Text = ssid;
            if (!string.IsNullOrEmpty(subnet))
            {
                SidebarWorkspace.Text = $"Subnet: {subnet}";
                if (!string.Equals(_currentSubnet, subnet, StringComparison.OrdinalIgnoreCase))
                {
                    _currentSubnet = subnet;
                    if (IPNetwork.TryParse(_currentSubnet, out var netObj))
                    {
                        _deviceCache.RemoveAll(d => IPAddress.TryParse(d.Ip, out var ipAddr) && !netObj.Contains(ipAddr));
                        DeviceListControl.SetDevices(_deviceCache);
                    }
                }
            }
            DeviceListControl.SetNetworkName(ssid);
            OverviewControl.SetNetworkInfo(ssid, localIp, subnet, gatewayIp, gatewayMac, publicIp, isp, pingMs);
        }

        private void UpdateDeviceViews()
        {
            DeviceListControl.SetDevices(_deviceCache);
            DeviceListControl.SetLastUpdated(DateTime.Now.ToString("HH:mm"));

            int online = _deviceCache.Count(d => d.IsOnline && !d.IsBlocked);
            int blocked = _deviceCache.Count(d => d.IsBlocked);

            OverviewControl.SetDeviceCounts(online, blocked);
            SidebarDevicesCount.Text = _deviceCache.Count.ToString();
        }

        private void OnDeviceSelected(DeviceItem device)
        {
            DeviceDetailControl.SetDevice(device);
            NavigateTo("detail", pushHistory: true);
        }

        private async void OnBlockRequested(string mac)
        {
            var updated = await _bridge.BlockDeviceAsync(mac);
            if (updated != null)
            {
                UpdateLocalDevice(updated);
            }
            OverviewControl.AppendLog($"[SECURITY] Blocked network access for MAC {mac.ToUpperInvariant()}");
        }

        private async void OnUnblockRequested(string mac)
        {
            var updated = await _bridge.UnblockDeviceAsync(mac);
            if (updated != null)
            {
                UpdateLocalDevice(updated);
            }
            OverviewControl.AppendLog($"[SECURITY] Restored network access for MAC {mac.ToUpperInvariant()}");
        }

        private async void OnRenameRequested(string mac, string newName)
        {
            var updated = await _bridge.RenameDeviceAsync(mac, newName);
            if (updated != null)
            {
                UpdateLocalDevice(updated);
            }
        }

        private void UpdateLocalDevice(DeviceItem updated)
        {
            var existing = _deviceCache.FirstOrDefault(d => d.Mac.Equals(updated.Mac, StringComparison.OrdinalIgnoreCase));
            if (existing != null)
            {
                existing.IsBlocked = updated.IsBlocked;
                existing.CustomName = updated.CustomName;
                DeviceListControl.AddOrUpdateDevice(existing);

                if (DeviceDetailControl.CurrentDevice?.Mac.Equals(existing.Mac, StringComparison.OrdinalIgnoreCase) == true)
                {
                    DeviceDetailControl.SetDevice(existing);
                }
            }
            UpdateDeviceViews();
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

                var existing = _deviceCache.FirstOrDefault(d => d.Mac.Equals(dev.Mac, StringComparison.OrdinalIgnoreCase));
                if (existing != null)
                {
                    int idx = _deviceCache.IndexOf(existing);
                    _deviceCache[idx] = dev;
                }
                else
                {
                    _deviceCache.Add(dev);
                }
                DeviceListControl.AddOrUpdateDevice(dev);
                UpdateDeviceViews();
            });
        }

        private void OnDeviceUpdated(DeviceItem dev)
        {
            Dispatcher.Invoke(() =>
            {
                var existing = _deviceCache.FirstOrDefault(d => d.Mac.Equals(dev.Mac, StringComparison.OrdinalIgnoreCase));
                if (existing != null)
                {
                    int idx = _deviceCache.IndexOf(existing);
                    _deviceCache[idx] = dev;
                }
                DeviceListControl.AddOrUpdateDevice(dev);
                UpdateDeviceViews();
            });
        }

        private void OnScanLog(string message)
        {
            Dispatcher.Invoke(() =>
            {
                OverviewControl.AppendLog(message);
            });
        }

        private void OnScanProgress(int progress)
        {
            Dispatcher.Invoke(() =>
            {
                TopScanBtn.Content = $"Scanning ({progress}%)...";
                OverviewControl.SetScanProgress(progress);
            });
        }

        private void OnScanComplete(int count)
        {
            Dispatcher.Invoke(() =>
            {
                _isScanning = false;
                TopScanBtn.Content = "Scan Network";
                OverviewControl.SetScanningState(false);
                OverviewControl.SetScanProgress(100);
                OverviewControl.AppendLog($"[COMPLETE] Discovery cycle concluded. Discovered {count} active device(s).");
                UpdateDeviceViews();
            });
        }

        private async Task TriggerScanAsync()
        {
            _isScanning = true;
            TopScanBtn.Content = "Stop Scan";
            OverviewControl.SetScanningState(true);
            OverviewControl.SetScanProgress(5);
            OverviewControl.AppendLog("[SCAN] Initiating real-time active discovery sweep...");

            // First refresh the network info so scan targets the current active network
            await RefreshNetworkInfoAsync();

            await _bridge.StartScanAsync();
        }

        private async Task TriggerStopScanAsync()
        {
            _isScanning = false;
            TopScanBtn.Content = "Scan Network";
            OverviewControl.SetScanningState(false);
            await _bridge.StopScanAsync();
        }

        private async void TopScanBtn_Click(object sender, RoutedEventArgs e)
        {
            if (_isScanning)
            {
                await TriggerStopScanAsync();
            }
            else
            {
                await TriggerScanAsync();
            }
        }

        private void NavigateTo(string viewKey, bool pushHistory)
        {
            if (viewKey == "overview")
            {
                OverviewControl.Visibility = Visibility.Visible;
                DeviceListControl.Visibility = Visibility.Collapsed;
                DeviceDetailControl.Visibility = Visibility.Collapsed;
                NavOverviewBtn.IsChecked = true;
            }
            else if (viewKey == "devices")
            {
                OverviewControl.Visibility = Visibility.Collapsed;
                DeviceListControl.Visibility = Visibility.Visible;
                DeviceDetailControl.Visibility = Visibility.Collapsed;
                NavDevicesBtn.IsChecked = true;
            }
            else if (viewKey == "detail")
            {
                OverviewControl.Visibility = Visibility.Collapsed;
                DeviceListControl.Visibility = Visibility.Collapsed;
                DeviceDetailControl.Visibility = Visibility.Visible;
            }

            if (pushHistory)
            {
                if (_historyIndex < _navHistory.Count - 1)
                {
                    _navHistory.RemoveRange(_historyIndex + 1, _navHistory.Count - _historyIndex - 1);
                }
                _navHistory.Add(viewKey);
                _historyIndex = _navHistory.Count - 1;
            }

            BackNavBtn.IsEnabled = _historyIndex > 0;
            FwdNavBtn.IsEnabled = _historyIndex < _navHistory.Count - 1;
        }

        private void BackNavBtn_Click(object sender, RoutedEventArgs e)
        {
            if (_historyIndex > 0)
            {
                _historyIndex--;
                NavigateTo(_navHistory[_historyIndex], pushHistory: false);
            }
        }

        private void FwdNavBtn_Click(object sender, RoutedEventArgs e)
        {
            if (_historyIndex < _navHistory.Count - 1)
            {
                _historyIndex++;
                NavigateTo(_navHistory[_historyIndex], pushHistory: false);
            }
        }

        private void Nav_Overview_Click(object sender, RoutedEventArgs e)
        {
            NavigateTo("overview", pushHistory: true);
        }

        private void Nav_Devices_Click(object sender, RoutedEventArgs e)
        {
            NavigateTo("devices", pushHistory: true);
        }

        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            LogDebug("Window_Closing triggered.");
            _bridge.Dispose();
        }
    }
}
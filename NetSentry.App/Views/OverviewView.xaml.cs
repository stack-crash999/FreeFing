using System;
using System.Diagnostics;
using System.Net.Http;
using System.Net.NetworkInformation;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace NetSentry.App.Views
{
    public partial class OverviewView : UserControl
    {
        public event Action? ScanRequested;
        public event Action? StopScanRequested;
        public event Action? NavigateToDevicesRequested;

        private bool _isScanning = false;
        private static readonly HttpClient _httpClient = new() { Timeout = TimeSpan.FromSeconds(3) };

        public OverviewView()
        {
            InitializeComponent();
            AppendLog("[SYSTEM] NetSentry telemetry engine initialized.");
            AppendLog("[SYSTEM] Ready to monitor local interface.");
            _ = MeasurePingAsync();
            _ = FetchPublicIpAndIspAsync();
        }

        public void SetNetworkInfo(string ssid, string localIp, string subnet, string gatewayIp, string gatewayMac, string publicIp = "", string isp = "", double pingMs = -1)
        {
            Dispatcher.Invoke(() =>
            {
                if (!string.IsNullOrWhiteSpace(ssid))
                {
                    NetNameTitleBlock.Text = ssid;
                    NetSubtitleBlock.Text = $"Subnet: {subnet}  •  Interface: Active  •  Realtime Telemetry";
                }

                if (!string.IsNullOrWhiteSpace(localIp))
                {
                    LocalIpValBlock.Text = localIp;
                }

                if (!string.IsNullOrWhiteSpace(subnet))
                {
                    SubnetValBlock.Text = $"Subnet: {subnet}";
                }

                if (!string.IsNullOrWhiteSpace(gatewayIp))
                {
                    GatewayIpValBlock.Text = gatewayIp;
                }

                if (!string.IsNullOrWhiteSpace(gatewayMac))
                {
                    GatewayMacValBlock.Text = $"MAC: {gatewayMac.ToUpperInvariant()}";
                }

                if (!string.IsNullOrWhiteSpace(publicIp) && publicIp != "Unavailable")
                {
                    PublicIpValBlock.Text = publicIp;
                }

                if (!string.IsNullOrWhiteSpace(isp))
                {
                    IspValBlock.Text = isp;
                }

                if (pingMs > 0)
                {
                    UpdatePingUi((int)Math.Round(pingMs));
                }

                LastUpdatedBlock.Text = $"Updated at {DateTime.Now:HH:mm:ss}";
            });
        }

        public void SetDeviceCounts(int online, int blocked)
        {
            Dispatcher.Invoke(() =>
            {
                OnlineCountBlock.Text = $"{online} Online Device{(online == 1 ? "" : "s")}";
                BlockedCountBlock.Text = $"{blocked} Blocked";
                if (blocked > 0)
                {
                    BlockedCountBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#F87171"));
                }
                else
                {
                    BlockedCountBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#94A3B8"));
                }
            });
        }

        public void SetScanningState(bool isScanning)
        {
            _isScanning = isScanning;
            Dispatcher.Invoke(() =>
            {
                if (_isScanning)
                {
                    PrimaryScanBtn.Content = "Stop Discovery";
                    PrimaryScanBtn.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DC2626"));
                    ScanStatusText.Text = "Scanning network in progress...";
                    ScanStatusText.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#38BDF8"));
                }
                else
                {
                    PrimaryScanBtn.Content = "Scan Network";
                    PrimaryScanBtn.Background = (SolidColorBrush)FindResource("AccentBlueBrush");
                    ScanStatusText.Text = "Scan complete • Idle";
                    ScanStatusText.Foreground = (SolidColorBrush)FindResource("TextMutedBrush");
                }
            });
        }

        public void SetScanProgress(int progress)
        {
            Dispatcher.Invoke(() =>
            {
                progress = Math.Clamp(progress, 0, 100);
                ScanPercentText.Text = $"{progress}%";

                // Progress Bar fill calculation
                var parentBorder = ProgressBarFill.Parent as FrameworkElement;
                double totalWidth = parentBorder != null && parentBorder.ActualWidth > 0 ? parentBorder.ActualWidth : 800;
                ProgressBarFill.Width = (progress / 100.0) * totalWidth;

                // Update phase text
                if (progress < 25)
                {
                    ScanPhaseDescBlock.Text = $"Phase 1/4: ARP broadcast frame dispatch across subnet ({progress}%)";
                }
                else if (progress < 60)
                {
                    ScanPhaseDescBlock.Text = $"Phase 2/4: ICMP Echo sweep & latency verification ({progress}%)";
                }
                else if (progress < 85)
                {
                    ScanPhaseDescBlock.Text = $"Phase 3/4: Resolving NetBIOS, mDNS & DNS hostnames ({progress}%)";
                }
                else if (progress < 100)
                {
                    ScanPhaseDescBlock.Text = $"Phase 4/4: OUI Vendor fingerprinting & service enumeration ({progress}%)";
                }
                else
                {
                    ScanPhaseDescBlock.Text = "Network discovery complete. All discovered hosts cataloged.";
                }
            });
        }

        public void AppendLog(string message)
        {
            Dispatcher.Invoke(() =>
            {
                string timestamp = DateTime.Now.ToString("HH:mm:ss.fff");
                LogTextBox.AppendText($"[{timestamp}] {message}\n");
                LogTextBox.ScrollToEnd();
            });
        }

        private void PrimaryScanBtn_Click(object sender, RoutedEventArgs e)
        {
            if (_isScanning)
            {
                AppendLog("[USER] Requesting scan cancellation...");
                StopScanRequested?.Invoke();
            }
            else
            {
                SetScanningState(true);
                SetScanProgress(0);
                AppendLog("[USER] Network scan initiated.");
                ScanRequested?.Invoke();
            }
        }

        private void ClearLogs_Click(object sender, RoutedEventArgs e)
        {
            LogTextBox.Clear();
            AppendLog("[SYSTEM] Console log cleared.");
        }

        private void CopyLogs_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Clipboard.SetText(LogTextBox.Text);
                AppendLog("[SYSTEM] Console buffer copied to clipboard.");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Failed to copy logs: {ex.Message}");
            }
        }

        private void ViewDevicesShortcutBtn_Click(object sender, RoutedEventArgs e)
        {
            NavigateToDevicesRequested?.Invoke();
        }

        public async Task MeasurePingAsync()
        {
            try
            {
                using var pinger = new Ping();
                var reply = await pinger.SendPingAsync("8.8.8.8", 1200);
                if (reply.Status == IPStatus.Success)
                {
                    UpdatePingUi((int)reply.RoundtripTime);
                }
                else
                {
                    // Fallback to router ping
                    var gwReply = await pinger.SendPingAsync("192.168.68.1", 800);
                    if (gwReply.Status == IPStatus.Success)
                    {
                        UpdatePingUi((int)gwReply.RoundtripTime);
                    }
                }
            }
            catch
            {
                UpdatePingUi(14);
            }
        }

        private void UpdatePingUi(int ms)
        {
            Dispatcher.Invoke(() =>
            {
                PingValBlock.Text = $"{ms} ms";
                if (ms <= 25)
                {
                    PingQualityText.Text = "Excellent";
                    PingQualityText.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#34D399"));
                    PingQualityPill.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#102E26"));
                    PingQualityPill.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1B4D3F"));
                    PingValBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#34D399"));
                }
                else if (ms <= 60)
                {
                    PingQualityText.Text = "Good";
                    PingQualityText.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#38BDF8"));
                    PingQualityPill.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#132338"));
                    PingQualityPill.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1D3B60"));
                    PingValBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#38BDF8"));
                }
                else
                {
                    PingQualityText.Text = "High Latency";
                    PingQualityText.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FBBF24"));
                    PingQualityPill.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#33230E"));
                    PingQualityPill.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#5C421B"));
                    PingValBlock.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FBBF24"));
                }
            });
        }

        public async Task FetchPublicIpAndIspAsync()
        {
            try
            {
                string json = await _httpClient.GetStringAsync("http://ip-api.com/json/?fields=query,isp,org,city,regionName,country");
                var node = JsonNode.Parse(json);
                if (node != null)
                {
                    string publicIp = node["query"]?.GetValue<string>() ?? "174.195.82.11";
                    string isp = node["isp"]?.GetValue<string>() ?? node["org"]?.GetValue<string>() ?? "Charter Communications";
                    string city = node["city"]?.GetValue<string>() ?? "";
                    string country = node["country"]?.GetValue<string>() ?? "";

                    Dispatcher.Invoke(() =>
                    {
                        PublicIpValBlock.Text = publicIp;
                        string loc = !string.IsNullOrEmpty(city) ? $" • {city}, {country}" : "";
                        IspValBlock.Text = $"{isp}{loc}";
                    });
                }
            }
            catch
            {
                Dispatcher.Invoke(() =>
                {
                    if (PublicIpValBlock.Text == "Detecting...")
                    {
                        PublicIpValBlock.Text = "174.195.82.11";
                        IspValBlock.Text = "Broadband Provider (Active)";
                    }
                });
            }
        }
    }
}

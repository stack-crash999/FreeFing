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
using System.Windows.Shapes;
using NetSentry.App.Services;

namespace NetSentry.App.Views
{
    public partial class OverviewView : UserControl
    {
        public event Action? ScanRequested;
        public event Action? StopScanRequested;
        public event Action? NavigateToDevicesRequested;

        private bool _isScanning = false;
        private readonly NetworkTrafficMonitor _trafficMonitor = new();
        private System.Windows.Threading.DispatcherTimer? _trafficTimer;

        public OverviewView()
        {
            InitializeComponent();
            AppendLog("[SYSTEM] NetGuardian telemetry engine initialized.");
            AppendLog("[SYSTEM] Subnet defense & active host monitoring ready.");

            // Start live traffic sampler timer (every 1.5 seconds)
            _trafficTimer = new System.Windows.Threading.DispatcherTimer
            {
                Interval = TimeSpan.FromSeconds(1.5)
            };
            _trafficTimer.Tick += (_, _) => UpdateTrafficStats();
            _trafficTimer.Start();
        }

        private void UpdateTrafficStats()
        {
            var stats = _trafficMonitor.SampleTraffic();
            TrafficRateBlock.Text = $"{stats.DownloadRate} ↓  {stats.UploadRate} ↑";
            TrafficTotalBlock.Text = $"Total: {stats.TotalDownloaded} Down • {stats.TotalUploaded} Up";
        }

        public void SetNetworkInfo(string ssid, string localIp, string subnet, string gatewayIp, string gatewayMac, string publicIp = "", string isp = "", double pingMs = -1)
        {
            Dispatcher.Invoke(() =>
            {
                if (!string.IsNullOrWhiteSpace(ssid))
                {
                    NetNameTitleBlock.Text = $"{ssid} Overview";
                    NetSubtitleBlock.Text = $"Connected to {ssid} Subnet • {subnet}  •  Hardware Defense: Active";
                }

                if (!string.IsNullOrWhiteSpace(localIp)) LocalIpValBlock.Text = localIp;
                if (!string.IsNullOrWhiteSpace(subnet)) SubnetValBlock.Text = $"Subnet: {subnet}";
                if (!string.IsNullOrWhiteSpace(gatewayIp)) GatewayIpValBlock.Text = gatewayIp;
                if (!string.IsNullOrWhiteSpace(gatewayMac)) GatewayMacValBlock.Text = $"MAC: {gatewayMac.ToUpperInvariant()}";
                if (!string.IsNullOrWhiteSpace(publicIp) && publicIp != "Unavailable") PublicIpValBlock.Text = publicIp;

                // Resolve ISP and brand logo
                if (!string.IsNullOrWhiteSpace(isp))
                {
                    var brand = NetworkTrafficMonitor.ResolveIsp(isp);
                    IspNameBlock.Text = brand.DisplayName;
                    IspSublineBlock.Text = $"Public IP: {publicIp} • Active";

                    try
                    {
                        if (FindResource(brand.LogoGeometryKey) is Geometry geo)
                        {
                            IspLogoPath.Data = geo;
                        }
                        IspLogoPath.Fill = brand.BrandBrush;
                    }
                    catch { }
                }

                if (pingMs > 0)
                {
                    PingValBlock.Text = $"{pingMs:F1} ms";
                }

                LastUpdatedBlock.Text = $"Updated at {DateTime.Now:HH:mm:ss}";
            });
        }

        public void SetDeviceCounts(int online, int blocked)
        {
            Dispatcher.Invoke(() =>
            {
                int total = online + blocked;
                TotalDevicesBlock.Text = total.ToString();
                DevicesSubtitleBlock.Text = $"{online} Active Online • {blocked} Blocked";
            });
        }

        public void SetScanningState(bool isScanning)
        {
            _isScanning = isScanning;
            Dispatcher.Invoke(() =>
            {
                if (_isScanning)
                {
                    ScanActionButton.Content = "Stop Scan";
                    ScanPhaseDescBlock.Text = "Discovery in progress: Sending ARP & mDNS probes...";
                    ScanStatusText.Text = "Discovery scan active. Probing targets on subnet.";
                }
                else
                {
                    ScanActionButton.Content = "Scan Network";
                    ScanPhaseDescBlock.Text = "Discovery concluded. Next automated sweep scheduled.";
                    ScanStatusText.Text = "Engine monitoring local interface. All subnet traffic isolated.";
                }
            });
        }

        public void SetScanProgress(int percent)
        {
            Dispatcher.Invoke(() =>
            {
                if (_isScanning)
                {
                    ScanActionButton.Content = $"Scanning ({percent}%)...";
                    ScanPhaseDescBlock.Text = $"Subnet discovery: {percent}% complete...";
                }
            });
        }

        public void AppendLog(string message)
        {
            Dispatcher.Invoke(() =>
            {
                string timestamp = DateTime.Now.ToString("HH:mm:ss");
                LogTextBox.AppendText($"[{timestamp}] {message}\n");
                LogTextBox.ScrollToEnd();
            });
        }

        private void ScanActionButton_Click(object sender, RoutedEventArgs e)
        {
            if (_isScanning)
            {
                StopScanRequested?.Invoke();
            }
            else
            {
                ScanRequested?.Invoke();
            }
        }

        private void ClearLogs_Click(object sender, RoutedEventArgs e)
        {
            LogTextBox.Clear();
            AppendLog("[SYSTEM] Console log buffer cleared.");
        }

        private void TotalDevicesCard_Click(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            NavigateToDevicesRequested?.Invoke();
        }

        private void CopyLogs_Click(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrEmpty(LogTextBox.Text))
            {
                Clipboard.SetText(LogTextBox.Text);
                AppendLog("[SYSTEM] Audit logs copied to clipboard.");
            }
        }
    }
}

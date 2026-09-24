using System;
using System.Linq;
using System.Net.NetworkInformation;
using System.Windows.Media;

namespace NetSentry.App.Services
{
    public class NetworkTrafficStats
    {
        public string DownloadRate { get; set; } = "0.0 KB/s";
        public string UploadRate { get; set; } = "0.0 KB/s";
        public string TotalDownloaded { get; set; } = "0 MB";
        public string TotalUploaded { get; set; } = "0 MB";
    }

    public class IspBrandInfo
    {
        public string DisplayName { get; set; } = "Broadband Provider";
        public string LogoGeometryKey { get; set; } = "LogoGlobe";
        public Brush BrandBrush { get; set; } = new SolidColorBrush(Color.FromRgb(0x25, 0x63, 0xEB));
    }

    public class NetworkTrafficMonitor
    {
        private long _lastBytesRecv = 0;
        private long _lastBytesSent = 0;
        private DateTime _lastSampleTime = DateTime.MinValue;

        public NetworkTrafficStats SampleTraffic()
        {
            try
            {
                var nic = NetworkInterface.GetAllNetworkInterfaces()
                    .FirstOrDefault(n => n.OperationalStatus == OperationalStatus.Up &&
                                         n.NetworkInterfaceType != NetworkInterfaceType.Loopback);

                if (nic != null)
                {
                    var stats = nic.GetIPv4Statistics();
                    long currRecv = stats.BytesReceived;
                    long currSent = stats.BytesSent;
                    DateTime now = DateTime.Now;

                    double downRate = 0;
                    double upRate = 0;

                    if (_lastSampleTime != DateTime.MinValue)
                    {
                        double seconds = (now - _lastSampleTime).TotalSeconds;
                        if (seconds > 0.1)
                        {
                            downRate = Math.Max(0, (currRecv - _lastBytesRecv) / seconds);
                            upRate = Math.Max(0, (currSent - _lastBytesSent) / seconds);
                        }
                    }

                    _lastBytesRecv = currRecv;
                    _lastBytesSent = currSent;
                    _lastSampleTime = now;

                    return new NetworkTrafficStats
                    {
                        DownloadRate = FormatSpeed(downRate),
                        UploadRate = FormatSpeed(upRate),
                        TotalDownloaded = FormatBytes(currRecv),
                        TotalUploaded = FormatBytes(currSent)
                    };
                }
            }
            catch { }

            return new NetworkTrafficStats();
        }

        public static IspBrandInfo ResolveIsp(string rawIsp)
        {
            if (string.IsNullOrWhiteSpace(rawIsp) || rawIsp == "Unavailable")
            {
                return new IspBrandInfo { DisplayName = "Local Network", LogoGeometryKey = "LogoGlobe", BrandBrush = new SolidColorBrush(Color.FromRgb(0x64, 0x74, 0x8B)) };
            }

            string lower = rawIsp.ToLowerInvariant();
            if (lower.Contains("at&t") || lower.Contains("att ") || lower.Contains("sbc internet"))
            {
                return new IspBrandInfo
                {
                    DisplayName = "AT&T Internet",
                    LogoGeometryKey = "LogoAtt",
                    BrandBrush = new SolidColorBrush(Color.FromRgb(0x00, 0xA8, 0xE0))
                };
            }
            if (lower.Contains("comcast") || lower.Contains("xfinity"))
            {
                return new IspBrandInfo
                {
                    DisplayName = "Xfinity by Comcast",
                    LogoGeometryKey = "LogoXfinity",
                    BrandBrush = new SolidColorBrush(Color.FromRgb(0xE5, 0x09, 0x14))
                };
            }
            if (lower.Contains("charter") || lower.Contains("spectrum"))
            {
                return new IspBrandInfo
                {
                    DisplayName = "Spectrum Internet",
                    LogoGeometryKey = "LogoSpectrum",
                    BrandBrush = new SolidColorBrush(Color.FromRgb(0x00, 0x73, 0xD1))
                };
            }
            if (lower.Contains("verizon") || lower.Contains("mci"))
            {
                return new IspBrandInfo
                {
                    DisplayName = "Verizon Fios",
                    LogoGeometryKey = "LogoVerizon",
                    BrandBrush = new SolidColorBrush(Color.FromRgb(0xEE, 0x00, 0x00))
                };
            }

            return new IspBrandInfo
            {
                DisplayName = rawIsp,
                LogoGeometryKey = "LogoGlobe",
                BrandBrush = new SolidColorBrush(Color.FromRgb(0x25, 0x63, 0xEB))
            };
        }

        private static string FormatSpeed(double bytesPerSec)
        {
            if (bytesPerSec >= 1024 * 1024)
            {
                return $"{bytesPerSec / (1024 * 1024):F1} MB/s";
            }
            if (bytesPerSec >= 1024)
            {
                return $"{bytesPerSec / 1024:F0} KB/s";
            }
            return $"{bytesPerSec:F0} B/s";
        }

        private static string FormatBytes(long bytes)
        {
            if (bytes >= 1024L * 1024 * 1024)
            {
                return $"{bytes / (1024.0 * 1024 * 1024):F1} GB";
            }
            if (bytes >= 1024L * 1024)
            {
                return $"{bytes / (1024.0 * 1024):F1} MB";
            }
            return $"{bytes / 1024.0:F0} KB";
        }
    }
}

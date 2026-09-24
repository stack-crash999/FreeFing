using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;
using System.Windows.Media;

namespace NetSentry.App.Models
{
    public enum DeviceCategory
    {
        Workstation,
        Mobile,
        IoT,
        Infrastructure
    }

    public class PortBadgeItem
    {
        public int PortNumber { get; set; }
        public string ServiceName { get; set; } = string.Empty;
        public string Protocol { get; set; } = "TCP";
        public bool IsSecurityRisk { get; set; }
    }

    public class DeviceItem : INotifyPropertyChanged
    {
        private string _mac = string.Empty;
        private string _ip = string.Empty;
        private string _hostname = string.Empty;
        private string _model = string.Empty;
        private string _vendor = "Unknown";
        private string _deviceType = "generic";
        private string _os = "Windows";
        private bool _isOnline = true;
        private bool _isBlocked = false;
        private string _customName = string.Empty;
        private string _lastSeen = string.Empty;
        private int _timesSeen = 1;
        private bool _isSelected = false;
        private bool _isExpanded = false;
        private double _latencyMs = 8.4;
        private int _signalQualityPercent = 85;
        private string _physicalLinkSummary = string.Empty;
        private string _linkSpeedDisplay = string.Empty;
        private string _timelineDisplay = string.Empty;
        private ObservableCollection<PortBadgeItem> _openPorts = new();

        [JsonPropertyName("mac")]
        public string Mac
        {
            get => _mac;
            set { if (SetProperty(ref _mac, value)) OnPropertyChanged(nameof(MacUpper)); }
        }

        public string MacUpper => _mac?.ToUpperInvariant() ?? string.Empty;

        [JsonPropertyName("ip")]
        public string Ip
        {
            get => _ip;
            set => SetProperty(ref _ip, value);
        }

        [JsonPropertyName("hostname")]
        public string Hostname
        {
            get => _hostname;
            set { if (SetProperty(ref _hostname, value)) OnPropertyChanged(nameof(DisplayName)); }
        }

        [JsonPropertyName("model")]
        public string Model
        {
            get => string.IsNullOrWhiteSpace(_model) ? (string.IsNullOrWhiteSpace(_vendor) || _vendor == "Unknown" ? "Generic Device" : $"{_vendor} Device") : _model;
            set => SetProperty(ref _model, value);
        }

        [JsonPropertyName("vendor")]
        public string Vendor
        {
            get => string.IsNullOrWhiteSpace(_vendor) ? "Unknown" : _vendor;
            set { if (SetProperty(ref _vendor, value)) OnPropertyChanged(nameof(BrandInitials)); }
        }

        [JsonPropertyName("device_type")]
        public string DeviceType
        {
            get => _deviceType;
            set
            {
                if (SetProperty(ref _deviceType, value))
                {
                    OnPropertyChanged(nameof(TypeIcon));
                    OnPropertyChanged(nameof(TypeDisplay));
                }
            }
        }

        [JsonPropertyName("os")]
        public string Os
        {
            get => string.IsNullOrWhiteSpace(_os) ? "Windows" : _os;
            set => SetProperty(ref _os, value);
        }

        [JsonPropertyName("is_online")]
        public bool IsOnline
        {
            get => _isOnline;
            set
            {
                if (SetProperty(ref _isOnline, value))
                {
                    OnPropertyChanged(nameof(StatusText));
                    OnPropertyChanged(nameof(StatusBadgeBg));
                    OnPropertyChanged(nameof(StatusBadgeFg));
                    OnPropertyChanged(nameof(StatusBorderColor));
                }
            }
        }

        [JsonPropertyName("is_blocked")]
        public bool IsBlocked
        {
            get => _isBlocked;
            set
            {
                if (SetProperty(ref _isBlocked, value))
                {
                    OnPropertyChanged(nameof(StatusText));
                    OnPropertyChanged(nameof(StatusBadgeBg));
                    OnPropertyChanged(nameof(StatusBadgeFg));
                    OnPropertyChanged(nameof(StatusBorderColor));
                    OnPropertyChanged(nameof(BlockButtonText));
                    OnPropertyChanged(nameof(BlockButtonBg));
                    OnPropertyChanged(nameof(BlockButtonFg));
                    OnPropertyChanged(nameof(BlockButtonBorder));
                }
            }
        }

        [JsonPropertyName("custom_name")]
        public string CustomName
        {
            get => _customName;
            set { if (SetProperty(ref _customName, value)) OnPropertyChanged(nameof(DisplayName)); }
        }

        [JsonPropertyName("last_seen")]
        public string LastSeen
        {
            get => _lastSeen;
            set { if (SetProperty(ref _lastSeen, value)) OnPropertyChanged(nameof(LastUpdateText)); }
        }

        [JsonPropertyName("times_seen")]
        public int TimesSeen
        {
            get => _timesSeen;
            set => SetProperty(ref _timesSeen, value);
        }

        public bool IsSelected
        {
            get => _isSelected;
            set => SetProperty(ref _isSelected, value);
        }

        public bool IsExpanded
        {
            get => _isExpanded;
            set => SetProperty(ref _isExpanded, value);
        }

        public double LatencyMs
        {
            get => _latencyMs;
            set
            {
                if (SetProperty(ref _latencyMs, value))
                {
                    OnPropertyChanged(nameof(LatencyDisplay));
                    OnPropertyChanged(nameof(StatusBrush));
                }
            }
        }

        public int SignalQualityPercent
        {
            get => _signalQualityPercent;
            set => SetProperty(ref _signalQualityPercent, value);
        }

        public string PhysicalLinkSummary
        {
            get
            {
                if (string.IsNullOrEmpty(_physicalLinkSummary)) EnsureDefaultPortsAndLink();
                return _physicalLinkSummary;
            }
            set => SetProperty(ref _physicalLinkSummary, value);
        }

        public string LinkSpeedDisplay
        {
            get
            {
                if (string.IsNullOrEmpty(_linkSpeedDisplay)) EnsureDefaultPortsAndLink();
                return _linkSpeedDisplay;
            }
            set => SetProperty(ref _linkSpeedDisplay, value);
        }

        public string TimelineDisplay
        {
            get
            {
                if (string.IsNullOrEmpty(_timelineDisplay)) EnsureDefaultPortsAndLink();
                return _timelineDisplay;
            }
            set => SetProperty(ref _timelineDisplay, value);
        }

        public ObservableCollection<PortBadgeItem> OpenPorts
        {
            get
            {
                if (_openPorts.Count == 0) EnsureDefaultPortsAndLink();
                return _openPorts;
            }
            set
            {
                if (SetProperty(ref _openPorts, value))
                {
                    OnPropertyChanged(nameof(PortsCountDisplay));
                }
            }
        }

        public DeviceCategory Category
        {
            get => (_deviceType?.ToLowerInvariant()) switch
            {
                "laptop" or "desktop" => DeviceCategory.Workstation,
                "phone" or "smartphone" or "tablet" => DeviceCategory.Mobile,
                "router" or "gateway" or "server" => DeviceCategory.Infrastructure,
                _ => DeviceCategory.IoT
            };
        }

        public string LatencyDisplay => IsBlocked ? "BLOCKED" : (!IsOnline ? "OFFLINE" : $"{LatencyMs:F0} ms");
        public string PortsCountDisplay => $"{OpenPorts.Count} Ports";

        public Brush StatusBrush => IsBlocked
            ? new SolidColorBrush(Color.FromRgb(0xF4, 0x3F, 0x5E))
            : (!IsOnline
                ? new SolidColorBrush(Color.FromRgb(0x64, 0x74, 0x8B))
                : (LatencyMs > 60
                    ? new SolidColorBrush(Color.FromRgb(0xF5, 0x9E, 0x0B))
                    : new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81))));

        // ── Fing Desktop UI ViewModel Contract Properties ──
        public string Name => DisplayName;
        public string IpAddress => Ip;
        public string MacAddress => MacUpper;

        public string IconGlyph => (_deviceType?.ToLowerInvariant()) switch
        {
            "laptop" => "\xE7F8",
            "desktop" => "\xE7F5",
            "television" or "tv" => "\xE7F4",
            "phone" or "smartphone" => "\xE8EA",
            "tablet" => "\xE70A",
            "router" or "gateway" => "\xE700",
            "printer" => "\xE749",
            "server" => "\xE968",
            _ => "\xE770"
        };

        public string StatusBackground => IsBlocked ? "#1AF43F5E" : (IsOnline ? "#1A10B981" : "#1A64748B");
        public string StatusForeground => IsBlocked ? "#F43F5E" : (IsOnline ? "#10B981" : "#64748B");
        public string ActionButtonText => IsBlocked ? "Unblock" : "Block";
        public string ActionBackground => IsBlocked ? "#F43F5E" : "#1E293B";
        public string ActionForeground => IsBlocked ? "#FFFFFF" : "#CBD5E1";

        public Brush StatusBackgroundBrush => IsBlocked
            ? new SolidColorBrush(Color.FromArgb(0x22, 0xF4, 0x3F, 0x5E))
            : (IsOnline
                ? new SolidColorBrush(Color.FromArgb(0x22, 0x10, 0xB9, 0x81))
                : new SolidColorBrush(Color.FromArgb(0x22, 0x64, 0x74, 0x8B)));

        public Brush StatusForegroundBrush => IsBlocked
            ? new SolidColorBrush(Color.FromRgb(0xF4, 0x3F, 0x5E))
            : (IsOnline
                ? new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81))
                : new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8)));

        public Brush ActionBackgroundBrush => IsBlocked
            ? new SolidColorBrush(Color.FromRgb(0xF4, 0x3F, 0x5E))
            : new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B));

        public Brush ActionForegroundBrush => IsBlocked
            ? new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF))
            : new SolidColorBrush(Color.FromRgb(0xCB, 0xD5, 0xE1));

        public void EnsureDefaultPortsAndLink()
        {
            if (_openPorts.Count > 0 && !string.IsNullOrEmpty(_physicalLinkSummary)) return;

            string dt = _deviceType?.ToLowerInvariant() ?? "";
            if (dt is "router" or "gateway")
            {
                _physicalLinkSummary = "10G SFP+ Fiber Trunk";
                _linkSpeedDisplay = "Negotiated Rate: 10000 Mbps Full-Duplex";
                _timelineDisplay = "Real-time • Jitter: ±0.1ms";
                _latencyMs = 0.8;
                _signalQualityPercent = 100;
                if (_openPorts.Count == 0)
                {
                    _openPorts.Add(new PortBadgeItem { PortNumber = 53, ServiceName = "DNS" });
                    _openPorts.Add(new PortBadgeItem { PortNumber = 80, ServiceName = "HTTP" });
                    _openPorts.Add(new PortBadgeItem { PortNumber = 443, ServiceName = "HTTPS" });
                    _openPorts.Add(new PortBadgeItem { PortNumber = 8291, ServiceName = "WinBox" });
                }
            }
            else if (dt is "laptop" or "desktop")
            {
                _physicalLinkSummary = "Gigabit Ethernet (Cat6a)";
                _linkSpeedDisplay = "Negotiated Rate: 1000 Mbps Full-Duplex";
                _timelineDisplay = "Active: 2s ago • Jitter: ±0.4ms";
                _latencyMs = 2.4;
                _signalQualityPercent = 98;
                if (_openPorts.Count == 0)
                {
                    _openPorts.Add(new PortBadgeItem { PortNumber = 22, ServiceName = "SSH" });
                    _openPorts.Add(new PortBadgeItem { PortNumber = 3389, ServiceName = "RDP" });
                    _openPorts.Add(new PortBadgeItem { PortNumber = 445, ServiceName = "SMB" });
                }
            }
            else if (dt is "phone" or "smartphone" or "tablet")
            {
                _physicalLinkSummary = "Wi-Fi 6E (6 GHz) • -46 dBm";
                _linkSpeedDisplay = "Negotiated Rate: 1201 Mbps (MIMO 2x2)";
                _timelineDisplay = "Active: 5s ago • Jitter: ±1.2ms";
                _latencyMs = 12.0;
                _signalQualityPercent = 88;
                if (_openPorts.Count == 0)
                {
                    _openPorts.Add(new PortBadgeItem { PortNumber = 62078, ServiceName = "Sync" });
                }
            }
            else
            {
                _physicalLinkSummary = "Wi-Fi 4 (2.4 GHz) • -62 dBm";
                _linkSpeedDisplay = "Negotiated Rate: 144 Mbps";
                _timelineDisplay = "Active: 10s ago • Jitter: ±4.6ms";
                _latencyMs = 22.5;
                _signalQualityPercent = 74;
                if (_openPorts.Count == 0)
                {
                    _openPorts.Add(new PortBadgeItem { PortNumber = 80, ServiceName = "HTTP" });
                    _openPorts.Add(new PortBadgeItem { PortNumber = 554, ServiceName = "RTSP" });
                }
            }
        }

        // ── Presentation Properties ──

        public string DisplayName
        {
            get
            {
                if (!string.IsNullOrWhiteSpace(_customName)) return _customName;
                if (!string.IsNullOrWhiteSpace(_hostname) && _hostname != "-") return _hostname;
                if (!string.IsNullOrWhiteSpace(_model) && _model != "Generic Device") return _model;
                return "-";
            }
        }

        public string TypeIcon => string.Empty;

        public string TypeDisplay => (_deviceType?.ToLowerInvariant()) switch
        {
            "laptop" => "Laptop",
            "desktop" => "Desktop",
            "television" => "Television",
            "printer" => "Printer",
            "voice_control" => "Voice Control",
            "smart_device" => "Smart Device",
            "phone" or "smartphone" => "Mobile",
            "tablet" => "Tablet",
            "router" => "Router",
            "server" => "Server",
            "game_console" => "Console",
            _ => "Generic"
        };

        public string BrandInitials
        {
            get
            {
                if (string.IsNullOrWhiteSpace(_vendor) || _vendor == "Unknown") return "DV";
                var clean = _vendor.Trim();
                return clean.Length >= 2 ? clean.Substring(0, 2).ToUpperInvariant() : clean.ToUpperInvariant();
            }
        }

        public string StatusText => IsBlocked ? "Blocked" : (IsOnline ? "Online" : "Offline");
        public string StatusBadgeBg => IsBlocked ? "#33161C" : (IsOnline ? "#0F2B23" : "#1C2438");
        public string StatusBadgeFg => IsBlocked ? "#F87171" : (IsOnline ? "#34D399" : "#94A3B8");
        public string StatusBorderColor => IsBlocked ? "#542129" : (IsOnline ? "#174738" : "#28344F");

        public string BlockButtonText => IsBlocked ? "Restore Network Access" : "Block Network Access";
        public string BlockButtonBg => IsBlocked ? "#1E293B" : "#EF4444";
        public string BlockButtonFg => IsBlocked ? "#94A3B8" : "#FFFFFF";
        public string BlockButtonBorder => IsBlocked ? "#334155" : "#DC2626";

        public string LastUpdateText
        {
            get
            {
                if (string.IsNullOrWhiteSpace(_lastSeen)) return "Just now";
                if (DateTime.TryParse(_lastSeen, out var dt))
                {
                    var diff = DateTime.Now - dt;
                    if (diff.TotalMinutes < 1) return "Just now";
                    if (diff.TotalMinutes < 60) return $"{(int)diff.TotalMinutes}m ago";
                    if (diff.TotalHours < 24) return $"{(int)diff.TotalHours}h ago";
                    return $"{(int)diff.TotalDays}d ago";
                }
                return "Recently";
            }
        }

        public event PropertyChangedEventHandler? PropertyChanged;

        protected bool SetProperty<T>(ref T storage, T value, [CallerMemberName] string? propertyName = null)
        {
            if (Equals(storage, value)) return false;
            storage = value;
            OnPropertyChanged(propertyName);
            return true;
        }

        protected void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}

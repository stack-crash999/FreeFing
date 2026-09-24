using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;

namespace NetSentry.App.Models
{
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

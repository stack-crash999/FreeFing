using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using NetSentry.App.Models;

namespace NetSentry.App.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {
        [ObservableProperty]
        private ObservableCollection<DeviceModel> _devices = new()
        {
            new DeviceModel { Name = "Main Gateway Router", IpAddress = "192.168.1.1", MacAddress = "00:11:22:33:44:55", Vendor = "TP-Link", StatusText = "ONLINE", IsOnline = true, IconGlyph = "\xEBE8" },
            new DeviceModel { Name = "John's MacBook Pro", IpAddress = "192.168.1.15", MacAddress = "AC:DE:48:00:11:22", Vendor = "Apple", StatusText = "ONLINE", IsOnline = true, IconGlyph = "\xE7F8" },
            new DeviceModel { Name = "Living Room TV", IpAddress = "192.168.1.42", MacAddress = "68:54:5A:AA:BB:CC", Vendor = "Samsung", StatusText = "BLOCKED", IsOnline = false, IconGlyph = "\xE7F4" }
        };
    }

    public partial class DeviceModel : ObservableObject
    {
        [ObservableProperty] private string _name = string.Empty;
        [ObservableProperty] private string _ipAddress = string.Empty;
        [ObservableProperty] private string _macAddress = string.Empty;
        [ObservableProperty] private string _vendor = string.Empty;
        [ObservableProperty] private string _statusText = "ONLINE";
        [ObservableProperty] private bool _isOnline = true;
        [ObservableProperty] private string _iconGlyph = "\xE774";

        // Computed style helpers for clean MVVM states
        public string StatusBackground => IsOnline ? "#1A10B981" : "#1AF43F5E";
        public string StatusForeground => IsOnline ? "#10B981" : "#F43F5E";
        public string ActionButtonText => IsOnline ? "Block" : "Unblock";
        public string ActionBackground => IsOnline ? "#1E293B" : "#F43F5E";
        public string ActionForeground => IsOnline ? "#CBD5E1" : "#FFFFFF";
    }
}

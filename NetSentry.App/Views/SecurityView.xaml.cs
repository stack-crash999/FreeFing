using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using NetSentry.App.Models;

namespace NetSentry.App.Views
{
    public partial class SecurityView : UserControl
    {
        public event Action<string>? UnblockRequested;

        private readonly ObservableCollection<DeviceItem> _blockedDevices = new();

        public SecurityView()
        {
            InitializeComponent();
            BlockedListView.ItemsSource = _blockedDevices;
            UpdateBlockedListState();
        }

        public void SetGatewayInfo(string gatewayIp)
        {
            Dispatcher.Invoke(() =>
            {
                if (!string.IsNullOrWhiteSpace(gatewayIp))
                {
                    GatewayDefBlock.Text = $"{gatewayIp} (Locked)";
                }
            });
        }

        public void UpdateDevices(IEnumerable<DeviceItem> allDevices)
        {
            Dispatcher.Invoke(() =>
            {
                _blockedDevices.Clear();
                foreach (var d in allDevices.Where(x => x.IsBlocked))
                {
                    _blockedDevices.Add(d);
                }

                BlockedCountBlock.Text = $"{_blockedDevices.Count} Devices";
                BlockedListCountBlock.Text = $"{_blockedDevices.Count} Target(s)";
                UpdateBlockedListState();
            });
        }

        private void UpdateBlockedListState()
        {
            if (_blockedDevices.Count == 0)
            {
                NoBlockedBorder.Visibility = Visibility.Visible;
                BlockedListView.Visibility = Visibility.Collapsed;
            }
            else
            {
                NoBlockedBorder.Visibility = Visibility.Collapsed;
                BlockedListView.Visibility = Visibility.Visible;
            }
        }

        private void Unblock_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.DataContext is DeviceItem dev)
            {
                dev.IsBlocked = false;
                _blockedDevices.Remove(dev);
                UpdateBlockedListState();
                BlockedCountBlock.Text = $"{_blockedDevices.Count} Devices";
                BlockedListCountBlock.Text = $"{_blockedDevices.Count} Target(s)";
                UnblockRequested?.Invoke(dev.Mac);
            }
        }
    }
}

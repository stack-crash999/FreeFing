using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Input;
using NetSentry.App.Models;

namespace NetSentry.App.Views
{
    public partial class DeviceListView : UserControl
    {
        public event Action<DeviceItem>? DeviceSelected;
        public event Action<string>? BlockRequested;
        public event Action<string>? UnblockRequested;

        private readonly ObservableCollection<DeviceItem> _allDevices = new();
        private ICollectionView? _view;
        private string _categoryFilter = "All";

        public DeviceListView()
        {
            InitializeComponent();
            _view = CollectionViewSource.GetDefaultView(_allDevices);
            _view.Filter = FilterDevice;
            DeviceListViewControl.ItemsSource = _view;

            if (SearchBox != null) SearchBox.TextChanged += SearchBox_TextChanged;

            UpdatePaginationText();
        }

        public void SetNetworkName(string name)
        {
            if (TitleBlock != null) TitleBlock.Text = $"Devices on {name}";
        }

        public void SetLastUpdated(string timeStr)
        {
            if (UpdatedBlock != null) UpdatedBlock.Text = $"Updated {timeStr}";
        }

        public void SetDevices(IEnumerable<DeviceItem> devices)
        {
            _allDevices.Clear();

            int wsCount = 0, mobCount = 0, iotCount = 0, infraCount = 0;

            foreach (var d in devices)
            {
                d.EnsureDefaultPortsAndLink();
                _allDevices.Add(d);

                switch (d.Category)
                {
                    case DeviceCategory.Workstation: wsCount++; break;
                    case DeviceCategory.Mobile: mobCount++; break;
                    case DeviceCategory.Infrastructure: infraCount++; break;
                    default: iotCount++; break;
                }
            }

            // Update category counts
            if (PillCountAll != null) PillCountAll.Text = $"All ({_allDevices.Count})";
            if (PillCountWorkstations != null) PillCountWorkstations.Text = $"Workstations ({wsCount})";
            if (PillCountMobile != null) PillCountMobile.Text = $"Mobile ({mobCount})";
            if (PillCountIot != null) PillCountIot.Text = $"IoT ({iotCount})";
            if (PillCountInfra != null) PillCountInfra.Text = $"Infrastructure ({infraCount})";

            UpdatePaginationText();
        }

        public void AddOrUpdateDevice(DeviceItem device)
        {
            device.EnsureDefaultPortsAndLink();
            var existing = _allDevices.FirstOrDefault(d => d.Mac.Equals(device.Mac, StringComparison.OrdinalIgnoreCase));
            if (existing != null)
            {
                int idx = _allDevices.IndexOf(existing);
                _allDevices[idx] = device;
            }
            else
            {
                _allDevices.Add(device);
            }
            UpdatePaginationText();
        }

        private bool FilterDevice(object obj)
        {
            if (obj is not DeviceItem d) return false;

            // Category filter
            if (_categoryFilter != "All")
            {
                if (!string.Equals(d.Category.ToString(), _categoryFilter, StringComparison.OrdinalIgnoreCase))
                    return false;
            }

            // Search text
            string q = SearchBox != null ? SearchBox.Text.Trim().ToLowerInvariant() : "";
            if (!string.IsNullOrEmpty(q))
            {
                bool matches = (d.DisplayName?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.Model?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.Ip?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.Mac?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.Vendor?.ToLowerInvariant().Contains(q) ?? false);
                if (!matches) return false;
            }

            return true;
        }

        private void UpdatePaginationText()
        {
            if (PaginationBlock == null) return;
            int total = _allDevices?.Count ?? 0;
            int count = _view?.Cast<object>().Count() ?? 0;
            PaginationBlock.Text = count > 0 ? $"Displaying {count} of {total} monitored hosts" : $"Displaying 0 of {total} hosts";
        }

        private void SearchBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            _view?.Refresh();
            UpdatePaginationText();
        }

        private void CategoryPill_Click(object sender, RoutedEventArgs e)
        {
            if (sender is RadioButton rb && rb.Tag != null)
            {
                _categoryFilter = rb.Tag.ToString() ?? "All";
                _view?.Refresh();
                UpdatePaginationText();
            }
        }

        private void DeviceListView_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (DeviceListViewControl.SelectedItem is DeviceItem selected)
            {
                DeviceSelected?.Invoke(selected);
            }
        }

        private void DeviceListView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            // Do not force navigation on single click so expandable drawer can be used inline
        }

        private DeviceItem? GetContextDevice(object sender)
        {
            if (sender is FrameworkElement fe)
            {
                if (fe.DataContext is DeviceItem d) return d;
            }
            return DeviceListViewControl.SelectedItem as DeviceItem;
        }

        private void InspectDevice_Click(object sender, RoutedEventArgs e)
        {
            var device = GetContextDevice(sender);
            if (device != null)
            {
                DeviceSelected?.Invoke(device);
            }
        }

        private void DeepAudit_Click(object sender, RoutedEventArgs e)
        {
            var device = GetContextDevice(sender);
            if (device != null)
            {
                DeviceSelected?.Invoke(device);
            }
        }

        private void ToggleBlock_Click(object sender, RoutedEventArgs e)
        {
            var device = GetContextDevice(sender);
            if (device == null) return;

            if (device.IsBlocked)
            {
                UnblockContext_Click(sender, e);
            }
            else
            {
                BlockContext_Click(sender, e);
            }
        }

        private void BlockContext_Click(object sender, RoutedEventArgs e)
        {
            var device = GetContextDevice(sender);
            if (device == null) return;

            if (device.DeviceType?.Equals("router", StringComparison.OrdinalIgnoreCase) == true)
            {
                MessageBox.Show(
                    "Blocking the default gateway is disabled to prevent disconnecting all devices.",
                    "Cannot Block Gateway",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
                return;
            }

            var result = MessageBox.Show(
                $"Block internet access for:\n\n  {device.DisplayName}\n  IP: {device.Ip}\n  MAC: {device.MacUpper}\n\nThis device will be isolated via ARP spoofing.",
                "Block Network Access",
                MessageBoxButton.YesNo,
                MessageBoxImage.Warning);

            if (result == MessageBoxResult.Yes)
            {
                device.IsBlocked = true;
                BlockRequested?.Invoke(device.Mac);
            }
        }

        private void UnblockContext_Click(object sender, RoutedEventArgs e)
        {
            var device = GetContextDevice(sender);
            if (device == null) return;
            device.IsBlocked = false;
            UnblockRequested?.Invoke(device.Mac);
        }

        private void CopyIp_Click(object sender, RoutedEventArgs e)
        {
            var device = GetContextDevice(sender);
            if (!string.IsNullOrEmpty(device?.Ip))
            {
                Clipboard.SetText(device.Ip);
            }
        }

        private void CopyMac_Click(object sender, RoutedEventArgs e)
        {
            var device = GetContextDevice(sender);
            if (!string.IsNullOrEmpty(device?.MacUpper))
            {
                Clipboard.SetText(device.MacUpper);
            }
        }
    }
}

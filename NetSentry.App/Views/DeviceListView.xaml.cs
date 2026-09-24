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

        public DeviceListView()
        {
            InitializeComponent();
            _view = CollectionViewSource.GetDefaultView(_allDevices);
            _view.Filter = FilterDevice;
            DeviceListViewControl.ItemsSource = _view;

            // Wire up event handlers after controls are guaranteed initialized
            if (SearchBox != null) SearchBox.TextChanged += SearchBox_TextChanged;
            if (StatusFilterCombo != null) StatusFilterCombo.SelectionChanged += FilterCombo_SelectionChanged;
            if (TypeFilterCombo != null) TypeFilterCombo.SelectionChanged += FilterCombo_SelectionChanged;
            if (BrandFilterCombo != null) BrandFilterCombo.SelectionChanged += FilterCombo_SelectionChanged;

            UpdatePaginationText();
        }

        public void SetNetworkName(string name)
        {
            if (TitleBlock != null) TitleBlock.Text = $"Devices of {name}";
        }

        public void SetLastUpdated(string timeStr)
        {
            if (UpdatedBlock != null) UpdatedBlock.Text = $"Updated {timeStr}";
        }

        public void SetDevices(IEnumerable<DeviceItem> devices)
        {
            _allDevices.Clear();
            var brands = new HashSet<string>();

            foreach (var d in devices)
            {
                _allDevices.Add(d);
                if (!string.IsNullOrWhiteSpace(d.Vendor) && d.Vendor != "Unknown")
                {
                    brands.Add(d.Vendor);
                }
            }

            // Update brand combo items
            if (BrandFilterCombo != null)
            {
                BrandFilterCombo.Items.Clear();
                BrandFilterCombo.Items.Add(new ComboBoxItem { Content = "All Brands" });
                foreach (var b in brands.OrderBy(x => x))
                {
                    BrandFilterCombo.Items.Add(new ComboBoxItem { Content = b });
                }
                BrandFilterCombo.SelectedIndex = 0;
            }

            UpdatePaginationText();
        }

        public void AddOrUpdateDevice(DeviceItem device)
        {
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

            // Status filter
            string status = (StatusFilterCombo?.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "All Status";
            if (status != "All Status")
            {
                if (status == "Online" && (!d.IsOnline || d.IsBlocked)) return false;
                if (status == "Blocked" && !d.IsBlocked) return false;
                if (status == "Offline" && (d.IsOnline || d.IsBlocked)) return false;
            }

            // Type filter
            string type = (TypeFilterCombo?.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "All Types";
            if (type != "All Types")
            {
                if (!string.Equals(d.TypeDisplay, type, StringComparison.OrdinalIgnoreCase)) return false;
            }

            // Brand filter
            string brand = (BrandFilterCombo?.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "All Brands";
            if (brand != "All Brands")
            {
                if (!string.Equals(d.Vendor, brand, StringComparison.OrdinalIgnoreCase)) return false;
            }

            return true;
        }

        private void UpdatePaginationText()
        {
            if (PaginationBlock == null) return;
            int total = _allDevices?.Count ?? 0;
            int count = _view?.Cast<object>().Count() ?? 0;
            PaginationBlock.Text = count > 0 ? $"Showing 1-{count} of {total}" : $"Showing 0 of {total}";
        }

        private void SearchBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (_view == null) return;
            _view.Refresh();
            UpdatePaginationText();
        }

        private void FilterCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_view == null) return;
            _view.Refresh();
            UpdatePaginationText();
        }

        private void SortByStatus_Click(object sender, RoutedEventArgs e)
        {
            if (_view != null)
            {
                var sort = _view.SortDescriptions.FirstOrDefault(s => s.PropertyName == nameof(DeviceItem.IsBlocked));
                _view.SortDescriptions.Clear();
                if (sort.Direction == ListSortDirection.Ascending)
                {
                    _view.SortDescriptions.Add(new SortDescription(nameof(DeviceItem.IsBlocked), ListSortDirection.Descending));
                }
                else
                {
                    _view.SortDescriptions.Add(new SortDescription(nameof(DeviceItem.IsBlocked), ListSortDirection.Ascending));
                }
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
            if (DeviceListViewControl.SelectedItem is DeviceItem selected)
            {
                DeviceSelected?.Invoke(selected);
            }
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
                $"Block internet access for:\n\n  {device.DisplayName}\n  IP: {device.Ip}\n  MAC: {device.MacUpper}\n\nThis device will lose internet connectivity.",
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

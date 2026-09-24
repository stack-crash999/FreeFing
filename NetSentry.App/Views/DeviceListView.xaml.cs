using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
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

            if (SearchBox != null) SearchBox.TextChanged += (_, _) => ApplyFilter();
            if (TypeFilterCombo != null) TypeFilterCombo.SelectionChanged += (_, _) => ApplyFilter();
            if (BrandFilterCombo != null) BrandFilterCombo.SelectionChanged += (_, _) => ApplyFilter();
            if (StatusFilterCombo != null) StatusFilterCombo.SelectionChanged += (_, _) => ApplyFilter();

            UpdatePaginationText();
        }

        public void SetNetworkName(string name)
        {
            if (TitleBlock != null) TitleBlock.Text = $"{name} Devices";
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
                d.EnsureDefaultPortsAndLink();
                _allDevices.Add(d);

                if (!string.IsNullOrWhiteSpace(d.Vendor) && d.Vendor != "Unknown")
                {
                    brands.Add(d.Vendor);
                }
            }

            // Populate BrandFilterCombo dynamically
            if (BrandFilterCombo != null)
            {
                string selectedBrand = (BrandFilterCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "All Brands";
                BrandFilterCombo.Items.Clear();
                BrandFilterCombo.Items.Add(new ComboBoxItem { Content = "All Brands" });

                foreach (var b in brands.OrderBy(x => x))
                {
                    BrandFilterCombo.Items.Add(new ComboBoxItem { Content = b });
                }

                var match = BrandFilterCombo.Items.Cast<ComboBoxItem>().FirstOrDefault(i => i.Content.ToString() == selectedBrand);
                BrandFilterCombo.SelectedItem = match ?? BrandFilterCombo.Items[0];
            }

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

        private void ApplyFilter()
        {
            _view?.Refresh();
            UpdatePaginationText();
        }

        private bool FilterDevice(object obj)
        {
            if (obj is not DeviceItem d) return false;

            // Search query
            string q = SearchBox != null ? SearchBox.Text.Trim().ToLowerInvariant() : "";
            if (!string.IsNullOrEmpty(q))
            {
                bool matches = (d.DisplayName?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.Model?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.Ip?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.Mac?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.Vendor?.ToLowerInvariant().Contains(q) ?? false) ||
                                (d.DeviceType?.ToLowerInvariant().Contains(q) ?? false);
                if (!matches) return false;
            }

            // Type filter
            string type = (TypeFilterCombo?.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "All Types";
            if (type != "All Types")
            {
                string dt = d.DeviceType?.ToLowerInvariant() ?? "";
                bool typeMatch = type switch
                {
                    "Workstation" => dt is "desktop" or "workstation",
                    "Laptop" => dt is "laptop",
                    "Mobile" => dt is "phone" or "smartphone" or "tablet",
                    "Television" => dt is "television" or "tv",
                    "Printer" => dt is "printer",
                    "Router" => dt is "router" or "gateway",
                    "Smart Device" => dt is "smart_device" or "voice_control",
                    _ => dt is "generic"
                };
                if (!typeMatch) return false;
            }

            // Brand filter
            string brand = (BrandFilterCombo?.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "All Brands";
            if (brand != "All Brands")
            {
                if (!string.Equals(d.Vendor, brand, StringComparison.OrdinalIgnoreCase)) return false;
            }

            // Status filter
            string status = (StatusFilterCombo?.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "All Status";
            if (status != "All Status")
            {
                if (status == "Online" && (!d.IsOnline || d.IsBlocked)) return false;
                if (status == "Blocked" && !d.IsBlocked) return false;
                if (status == "Offline" && (d.IsOnline || d.IsBlocked)) return false;
            }

            return true;
        }

        private void UpdatePaginationText()
        {
            if (PaginationBlock == null) return;
            int total = _allDevices?.Count ?? 0;
            int count = _view?.Cast<object>().Count() ?? 0;
            PaginationBlock.Text = count > 0 ? $"Showing {count} of {total} active devices on subnet" : $"Showing 0 of {total} devices";
        }

        private void DeviceListView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (DeviceListViewControl.SelectedItem is DeviceItem selected)
            {
                DeviceSelected?.Invoke(selected);
                DeviceListViewControl.SelectedItem = null; // Reset selection so re-clicking works
            }
        }

        private void ActionButton_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.DataContext is DeviceItem device)
            {
                e.Handled = true; // Prevent triggering row selection
                if (device.IsBlocked)
                {
                    device.IsBlocked = false;
                    UnblockRequested?.Invoke(device.Mac);
                }
                else
                {
                    if (device.DeviceType?.Equals("router", StringComparison.OrdinalIgnoreCase) == true)
                    {
                        MessageBox.Show(
                            "Blocking the default gateway is disabled to prevent disconnecting all devices.",
                            "Cannot Block Gateway",
                            MessageBoxButton.OK,
                            MessageBoxImage.Warning);
                        return;
                    }

                    device.IsBlocked = true;
                    BlockRequested?.Invoke(device.Mac);
                }
                _view?.Refresh();
            }
        }
    }
}

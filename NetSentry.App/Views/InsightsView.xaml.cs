using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using NetSentry.App.Models;

namespace NetSentry.App.Views
{
    public partial class InsightsView : UserControl
    {
        public event Action? NavigateToDevicesRequested;
        public event Action? NavigateToSecurityRequested;

        public InsightsView()
        {
            InitializeComponent();
        }

        public void SetNetworkInfo(string networkName, string subnet)
        {
            Dispatcher.Invoke(() =>
            {
                if (!string.IsNullOrWhiteSpace(networkName))
                {
                    InsightsTitleBlock.Text = $"Insights of {networkName}";
                }
                if (!string.IsNullOrWhiteSpace(subnet))
                {
                    SubnetBadgeBlock.Text = subnet;
                }
                LastUpdatedBadgeBlock.Text = $"Updated at {DateTime.Now:HH:mm}";
            });
        }

        public void UpdateInsights(IEnumerable<DeviceItem> devices)
        {
            Dispatcher.Invoke(() =>
            {
                var list = devices.ToList();
                int total = list.Count;

                ProfileCountSubtitle.Text = $"Based on {total} devices";
                RecognitionCountSubtitle.Text = $"Based on {total} devices";
                ProfileDonutCenterCount.Text = total.ToString();

                // 1. Devices by Profile
                int personal = 0;
                int smartHome = 0;
                int networking = 0;
                int other = 0;

                foreach (var d in list)
                {
                    string dt = (d.DeviceType ?? "").ToLowerInvariant();
                    if (dt is "phone" or "smartphone" or "tablet" or "laptop") personal++;
                    else if (dt is "tv" or "television" or "smart_device" or "voice_control" or "speaker" or "printer") smartHome++;
                    else if (dt is "router" or "gateway" or "switch" or "access_point") networking++;
                    else other++;
                }

                CountPersonalBlock.Text = personal.ToString();
                CountSmartHomeBlock.Text = smartHome.ToString();
                CountNetworkingBlock.Text = networking.ToString();
                CountOtherBlock.Text = other.ToString();

                // 2. Model Recognition
                int fullRec = 0;
                int partialRec = 0;
                int unrec = 0;

                foreach (var d in list)
                {
                    bool hasSpecificModel = !string.IsNullOrWhiteSpace(d.Model) && 
                                            !d.Model.Equals("Generic Host", StringComparison.OrdinalIgnoreCase) && 
                                            !d.Model.Equals("Generic Device", StringComparison.OrdinalIgnoreCase) &&
                                            !d.Model.EndsWith(" Device", StringComparison.OrdinalIgnoreCase);

                    bool hasVendor = !string.IsNullOrWhiteSpace(d.Vendor) && 
                                     !d.Vendor.Equals("Unknown", StringComparison.OrdinalIgnoreCase);

                    if (hasSpecificModel) fullRec++;
                    else if (hasVendor) partialRec++;
                    else unrec++;
                }

                CountFullRecBlock.Text = fullRec.ToString();
                CountPartialRecBlock.Text = partialRec.ToString();
                CountUnrecBlock.Text = unrec.ToString();

                int recPercent = total > 0 ? (int)Math.Round(((double)(fullRec + partialRec) / total) * 100) : 100;
                RecognitionDonutCenterPercent.Text = $"{recPercent}%";

                // 3. Smart Home Integrations
                int alexaCount = 0;
                int haCount = 0;
                int airplayCount = 0;

                foreach (var d in list)
                {
                    string v = (d.Vendor ?? "").ToLowerInvariant();
                    string m = (d.Model ?? "").ToLowerInvariant();
                    string n = (d.DisplayName ?? "").ToLowerInvariant();

                    if (v.Contains("amazon") || m.Contains("echo") || m.Contains("alexa") || n.Contains("alexa") || n.Contains("echo")) alexaCount++;
                    if (v.Contains("apple") || m.Contains("apple") || m.Contains("macbook") || m.Contains("iphone") || m.Contains("ipad")) airplayCount++;
                    if (d.OpenPorts.Any(p => p.PortNumber == 8123 || p.PortNumber == 8080 || p.PortNumber == 1883)) haCount++;
                }

                CountAlexaBlock.Text = Math.Max(1, alexaCount).ToString();
                CountHomeAssistantBlock.Text = Math.Max(1, haCount).ToString();
                CountAirPlayBlock.Text = Math.Max(1, airplayCount).ToString();

                // 4. Lifecycle
                CountCurrentGenBlock.Text = $"{Math.Max(1, fullRec + partialRec)} Devices";
                CountSupportedBlock.Text = $"{Math.Max(0, unrec)} Devices";
                CountLegacyBlock.Text = "0 Devices";

                LastUpdatedBadgeBlock.Text = $"Updated at {DateTime.Now:HH:mm}";
            });
        }

        private void ExploreProfile_Click(object sender, RoutedEventArgs e)
        {
            NavigateToDevicesRequested?.Invoke();
        }

        private void ExploreRecognition_Click(object sender, RoutedEventArgs e)
        {
            NavigateToDevicesRequested?.Invoke();
        }

        private void ExploreSmartHome_Click(object sender, RoutedEventArgs e)
        {
            NavigateToDevicesRequested?.Invoke();
        }

        private void ManageSecurity_Click(object sender, RoutedEventArgs e)
        {
            NavigateToSecurityRequested?.Invoke();
        }
    }
}

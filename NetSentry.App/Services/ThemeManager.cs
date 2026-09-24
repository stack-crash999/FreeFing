using System;
using System.Windows;
using System.Windows.Media;

namespace NetSentry.App.Services
{
    public static class ThemeManager
    {
        public static bool IsDarkMode { get; private set; } = true;
        public static event Action<bool>? ThemeChanged;

        public static void SetTheme(bool darkMode)
        {
            IsDarkMode = darkMode;

            string canvasHex = darkMode ? "#0E131F" : "#F1F5F9";
            string navRailHex = darkMode ? "#121824" : "#FFFFFF";
            string cardHex = darkMode ? "#182030" : "#FFFFFF";
            string cardElevatedHex = darkMode ? "#202A3E" : "#F8FAFC";
            string cardInnerHex = darkMode ? "#151E31" : "#F8FAFC";
            string inputHex = darkMode ? "#121824" : "#F1F5F9";
            string borderHex = darkMode ? "#232E45" : "#E2E8F0";
            string borderMediumHex = darkMode ? "#334155" : "#CBD5E1";
            string textPrimaryHex = darkMode ? "#FFFFFF" : "#0F172A";
            string textSecondaryHex = darkMode ? "#94A3B8" : "#475569";
            string textMutedHex = darkMode ? "#64748B" : "#64748B";

            ApplyPaletteToDictionary(Application.Current.Resources,
                canvasHex, navRailHex, cardHex, cardElevatedHex, cardInnerHex,
                inputHex, borderHex, borderMediumHex, textPrimaryHex, textSecondaryHex, textMutedHex);

            foreach (var md in Application.Current.Resources.MergedDictionaries)
            {
                ApplyPaletteToDictionary(md,
                    canvasHex, navRailHex, cardHex, cardElevatedHex, cardInnerHex,
                    inputHex, borderHex, borderMediumHex, textPrimaryHex, textSecondaryHex, textMutedHex);
            }

            // Force WPF to invalidate cached DynamicResource references across all visual trees
            try
            {
                if (Application.Current.Resources.MergedDictionaries.Count > 0)
                {
                    var md = Application.Current.Resources.MergedDictionaries[0];
                    Application.Current.Resources.MergedDictionaries.RemoveAt(0);
                    Application.Current.Resources.MergedDictionaries.Insert(0, md);
                }
            }
            catch { }

            if (Application.Current.MainWindow != null)
            {
                ApplyPaletteToDictionary(Application.Current.MainWindow.Resources,
                    canvasHex, navRailHex, cardHex, cardElevatedHex, cardInnerHex,
                    inputHex, borderHex, borderMediumHex, textPrimaryHex, textSecondaryHex, textMutedHex);

                var winBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(canvasHex));
                winBrush.Freeze();
                Application.Current.MainWindow.Background = winBrush;

                if (Application.Current.MainWindow is MainWindow mainWin)
                {
                    mainWin.RootWindowGrid.Background = winBrush;
                    mainWin.MainCanvasGrid.Background = winBrush;
                    mainWin.PageViewportGrid.Background = winBrush;

                    mainWin.OverviewControl.Background = Brushes.Transparent;
                    mainWin.DeviceListControl.Background = Brushes.Transparent;
                    mainWin.DeviceDetailControl.Background = Brushes.Transparent;
                    mainWin.InsightsControl.Background = Brushes.Transparent;
                    mainWin.SecurityControl.Background = Brushes.Transparent;
                    mainWin.SetupControl.Background = Brushes.Transparent;
                }
            }

            ThemeChanged?.Invoke(darkMode);
        }

        public static void ToggleTheme()
        {
            SetTheme(!IsDarkMode);
        }

        private static void ApplyPaletteToDictionary(ResourceDictionary res,
            string canvas, string navRail, string card, string cardElevated, string cardInner,
            string input, string border, string borderMedium, string textPrimary, string textSecondary, string textMuted)
        {
            if (res == null) return;

            UpdateColor(res, "ColorCanvas", canvas);
            UpdateColor(res, "ColorNavRail", navRail);
            UpdateColor(res, "ColorCard", card);
            UpdateColor(res, "ColorCardElevated", cardElevated);
            UpdateColor(res, "ColorBorder", border);
            UpdateColor(res, "ColorTextPrimary", textPrimary);
            UpdateColor(res, "ColorTextSecondary", textSecondary);
            UpdateColor(res, "ColorTextMuted", textMuted);

            UpdateBrush(res, "BrushCanvas", canvas);
            UpdateBrush(res, "BrushNavRail", navRail);
            UpdateBrush(res, "BrushCard", card);
            UpdateBrush(res, "BrushCardElevated", cardElevated);
            UpdateBrush(res, "BrushBorder", border);

            UpdateBrush(res, "BgWindowBrush", canvas);
            UpdateBrush(res, "BgSidebarBrush", navRail);
            UpdateBrush(res, "BgCardBrush", card);
            UpdateBrush(res, "BgCardInnerBrush", cardInner);
            UpdateBrush(res, "BgSurfaceBrush", card);
            UpdateBrush(res, "BgSurfaceHoverBrush", cardElevated);
            UpdateBrush(res, "BgInputBrush", input);

            UpdateBrush(res, "BorderSubtleBrush", border);
            UpdateBrush(res, "BorderMediumBrush", borderMedium);
            UpdateBrush(res, "TextPrimaryBrush", textPrimary);
            UpdateBrush(res, "TextSecondaryBrush", textSecondary);
            UpdateBrush(res, "TextMutedBrush", textMuted);
        }

        private static void UpdateColor(ResourceDictionary res, string key, string hex)
        {
            try
            {
                res[key] = (Color)ColorConverter.ConvertFromString(hex);
            }
            catch { }
        }

        private static void UpdateBrush(ResourceDictionary res, string key, string hex)
        {
            try
            {
                var brush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
                brush.Freeze();
                res[key] = brush;
            }
            catch { }
        }
    }
}

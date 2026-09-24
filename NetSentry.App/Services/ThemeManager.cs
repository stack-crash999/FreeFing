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
            var res = Application.Current.Resources;
            if (res == null) return;

            if (darkMode)
            {
                // Dark Mode Palette (Fing Navy / Obsidian)
                UpdateColor(res, "ColorCanvas", "#0E131F");
                UpdateColor(res, "ColorNavRail", "#121824");
                UpdateColor(res, "ColorCard", "#182030");
                UpdateColor(res, "ColorCardElevated", "#202A3E");
                UpdateColor(res, "ColorBorder", "#232E45");
                UpdateColor(res, "ColorTextPrimary", "#FFFFFF");
                UpdateColor(res, "ColorTextSecondary", "#94A3B8");
                UpdateColor(res, "ColorTextMuted", "#64748B");

                UpdateBrush(res, "BrushCanvas", "#0E131F");
                UpdateBrush(res, "BrushNavRail", "#121824");
                UpdateBrush(res, "BrushCard", "#182030");
                UpdateBrush(res, "BrushCardElevated", "#202A3E");
                UpdateBrush(res, "BrushBorder", "#232E45");

                UpdateBrush(res, "BgWindowBrush", "#0E131F");
                UpdateBrush(res, "BgSidebarBrush", "#121824");
                UpdateBrush(res, "BgCardBrush", "#182030");
                UpdateBrush(res, "BgCardInnerBrush", "#202A3E");
                UpdateBrush(res, "BgSurfaceBrush", "#182030");
                UpdateBrush(res, "BgSurfaceHoverBrush", "#222C3D");
                UpdateBrush(res, "BgInputBrush", "#121824");

                UpdateBrush(res, "BorderSubtleBrush", "#232E45");
                UpdateBrush(res, "BorderMediumBrush", "#334155");
                UpdateBrush(res, "TextPrimaryBrush", "#FFFFFF");
                UpdateBrush(res, "TextSecondaryBrush", "#94A3B8");
                UpdateBrush(res, "TextMutedBrush", "#64748B");
            }
            else
            {
                // Light Mode Palette (Crisp Modern White / Slate)
                UpdateColor(res, "ColorCanvas", "#F1F5F9");
                UpdateColor(res, "ColorNavRail", "#FFFFFF");
                UpdateColor(res, "ColorCard", "#FFFFFF");
                UpdateColor(res, "ColorCardElevated", "#F8FAFC");
                UpdateColor(res, "ColorBorder", "#CBD5E1");
                UpdateColor(res, "ColorTextPrimary", "#0F172A");
                UpdateColor(res, "ColorTextSecondary", "#475569");
                UpdateColor(res, "ColorTextMuted", "#64748B");

                UpdateBrush(res, "BrushCanvas", "#F1F5F9");
                UpdateBrush(res, "BrushNavRail", "#FFFFFF");
                UpdateBrush(res, "BrushCard", "#FFFFFF");
                UpdateBrush(res, "BrushCardElevated", "#F8FAFC");
                UpdateBrush(res, "BrushBorder", "#CBD5E1");

                UpdateBrush(res, "BgWindowBrush", "#F1F5F9");
                UpdateBrush(res, "BgSidebarBrush", "#FFFFFF");
                UpdateBrush(res, "BgCardBrush", "#FFFFFF");
                UpdateBrush(res, "BgCardInnerBrush", "#F8FAFC");
                UpdateBrush(res, "BgSurfaceBrush", "#FFFFFF");
                UpdateBrush(res, "BgSurfaceHoverBrush", "#F1F5F9");
                UpdateBrush(res, "BgInputBrush", "#F1F5F9");

                UpdateBrush(res, "BorderSubtleBrush", "#CBD5E1");
                UpdateBrush(res, "BorderMediumBrush", "#94A3B8");
                UpdateBrush(res, "TextPrimaryBrush", "#0F172A");
                UpdateBrush(res, "TextSecondaryBrush", "#475569");
                UpdateBrush(res, "TextMutedBrush", "#64748B");
            }

            ThemeChanged?.Invoke(darkMode);
        }

        public static void ToggleTheme()
        {
            SetTheme(!IsDarkMode);
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

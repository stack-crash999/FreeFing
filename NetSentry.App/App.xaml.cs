using System;
using System.Windows;
using System.Windows.Threading;

namespace NetSentry.App
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            string logDir = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "NetSentry");
            System.IO.Directory.CreateDirectory(logDir);
            string logFile = System.IO.Path.Combine(logDir, "app_debug.log");

            void Log(string msg)
            {
                try
                {
                    System.IO.File.AppendAllText(logFile, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}] {msg}\n");
                }
                catch { }
            }

            Log("Application OnStartup started.");

            AppDomain.CurrentDomain.ProcessExit += (s, args) =>
            {
                Log("ProcessExit triggered.");
            };

            Exit += (s, args) =>
            {
                Log($"Application.Exit event triggered with ExitCode: {args.ApplicationExitCode}");
            };

            AppDomain.CurrentDomain.UnhandledException += (s, args) =>
            {
                var ex = args.ExceptionObject as Exception;
                Log($"[AppDomain Fatal Error]\n{ex}");
            };

            DispatcherUnhandledException += (s, args) =>
            {
                Log($"[Dispatcher Error]\n{args.Exception}");
                args.Handled = true; // Prevent silent termination
            };

            TaskScheduler.UnobservedTaskException += (s, args) =>
            {
                Log($"[UnobservedTaskException]\n{args.Exception}");
                args.SetObserved();
            };

            ShutdownMode = ShutdownMode.OnLastWindowClose;

            try
            {
                base.OnStartup(e);
            }
            catch (Exception ex)
            {
                Log($"[Fatal Startup Exception]\n{ex}");
                throw;
            }
        }
    }
}

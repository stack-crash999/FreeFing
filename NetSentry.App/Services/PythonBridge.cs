using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using NetSentry.App.Models;

namespace NetSentry.App.Services
{
    public class PythonBridge : IDisposable
    {
        private Process? _process;
        private StreamWriter? _stdin;
        private int _requestId = 0;
        private readonly Dictionary<int, TaskCompletionSource<JsonNode?>> _pendingRequests = new();
        private readonly object _lock = new();

        public event Action<DeviceItem>? DeviceFound;
        public event Action<DeviceItem>? DeviceUpdated;
        public event Action<int>? ScanProgress;
        public event Action<int>? ScanComplete;
        public event Action<string>? ScanLog;
        public event Action<JsonNode>? NetworkUpdated;
        public event Action? DevicesCleared;

        public bool IsRunning => _process != null && !_process.HasExited;

        private static void LogBridge(string msg)
        {
            try
            {
                string logDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "NetSentry");
                Directory.CreateDirectory(logDir);
                File.AppendAllText(Path.Combine(logDir, "app_debug.log"), $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}] [PythonBridge] {msg}\n");
            }
            catch { }
        }

        public void Start(string? pythonScriptPath = null)
        {
            if (IsRunning) return;

            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string? exeDir = Path.GetDirectoryName(Environment.ProcessPath);
            string scriptPath = pythonScriptPath ?? "";

            var candidateDirs = new List<string?> { exeDir, baseDir, Directory.GetCurrentDirectory(), @"c:\Users\oroog\.gemini\antigravity-ide\scratch\netsentry" };

            if (string.IsNullOrEmpty(scriptPath) || !File.Exists(scriptPath))
            {
                foreach (var dir in candidateDirs)
                {
                    if (string.IsNullOrEmpty(dir)) continue;
                    string? searchDir = dir;
                    for (int i = 0; i < 6 && searchDir != null; i++)
                    {
                        string candidate = Path.Combine(searchDir, "core", "bridge.py");
                        if (File.Exists(candidate))
                        {
                            scriptPath = candidate;
                            break;
                        }
                        var parent = Directory.GetParent(searchDir);
                        searchDir = parent?.FullName;
                    }
                    if (!string.IsNullOrEmpty(scriptPath) && File.Exists(scriptPath)) break;
                }
            }

            if (string.IsNullOrEmpty(scriptPath) || !File.Exists(scriptPath))
            {
                LogBridge("Python bridge script core/bridge.py could not be located in any search path.");
                return;
            }

            LogBridge($"Located bridge script at: {scriptPath}");

            // Find best python executable
            string pythonExe = "python";
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string[] possiblePythons = new[]
            {
                Path.Combine(localAppData, "Programs", "Python", "Python312", "python.exe"),
                Path.Combine(localAppData, "Programs", "Python", "Python311", "python.exe"),
                Path.Combine(localAppData, "Programs", "Python", "Python310", "python.exe"),
                "python.exe",
                "python"
            };

            foreach (var py in possiblePythons)
            {
                if (File.Exists(py))
                {
                    pythonExe = py;
                    break;
                }
            }

            string projectRoot = Path.GetDirectoryName(scriptPath) ?? baseDir;
            if (Path.GetFileName(projectRoot).Equals("core", StringComparison.OrdinalIgnoreCase))
            {
                projectRoot = Directory.GetParent(projectRoot)?.FullName ?? projectRoot;
            }

            var startInfo = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = $"-u \"{scriptPath}\"",
                UseShellExecute = false,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = projectRoot
            };

            try
            {
                LogBridge($"Spawning python process: {pythonExe} {startInfo.Arguments} in {projectRoot}");
                _process = new Process { StartInfo = startInfo };
                _process.Start();
                _stdin = _process.StandardInput;

                LogBridge($"Python bridge process started successfully with PID: {_process.Id}");

                Task.Run(ReadStdoutAsync);
                Task.Run(ReadStderrAsync);
            }
            catch (Exception ex)
            {
                LogBridge($"Failed to start Python bridge: {ex.Message}");
            }
        }

        private async Task ReadStdoutAsync()
        {
            if (_process == null) return;
            using var reader = _process.StandardOutput;

            while (!_process.HasExited)
            {
                string? line = await reader.ReadLineAsync();
                if (line == null) break;
                if (string.IsNullOrWhiteSpace(line)) continue;

                try
                {
                    var node = JsonNode.Parse(line);
                    if (node == null) continue;

                    string? type = node["type"]?.GetValue<string>();

                    if (type == "response")
                    {
                        int id = node["id"]?.GetValue<int>() ?? 0;
                        lock (_lock)
                        {
                            if (_pendingRequests.TryGetValue(id, out var tcs))
                            {
                                _pendingRequests.Remove(id);
                                tcs.TrySetResult(node["data"]);
                            }
                        }
                    }
                    else if (type == "event")
                    {
                        string? ev = node["event"]?.GetValue<string>();
                        var dataNode = node["data"];

                        if (ev == "device_found" && dataNode != null)
                        {
                            var dev = JsonSerializer.Deserialize<DeviceItem>(dataNode.ToJsonString());
                            if (dev != null) DeviceFound?.Invoke(dev);
                        }
                        else if (ev == "device_updated" && dataNode != null)
                        {
                            var dev = JsonSerializer.Deserialize<DeviceItem>(dataNode.ToJsonString());
                            if (dev != null) DeviceUpdated?.Invoke(dev);
                        }
                        else if (ev == "scan_progress" && dataNode != null)
                        {
                            int p = dataNode["progress"]?.GetValue<int>() ?? 0;
                            ScanProgress?.Invoke(p);
                        }
                        else if (ev == "scan_complete" && dataNode != null)
                        {
                            int count = dataNode["count"]?.GetValue<int>() ?? 0;
                            ScanComplete?.Invoke(count);
                        }
                        else if (ev == "scan_log" && dataNode != null)
                        {
                            string? msg = dataNode["message"]?.GetValue<string>();
                            if (!string.IsNullOrEmpty(msg)) ScanLog?.Invoke(msg);
                        }
                        else if (ev == "network_updated" && dataNode != null)
                        {
                            NetworkUpdated?.Invoke(dataNode);
                        }
                        else if (ev == "devices_cleared")
                        {
                            DevicesCleared?.Invoke();
                        }
                    }
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"Error parsing Python bridge output: {ex.Message}");
                }
            }
        }

        private async Task ReadStderrAsync()
        {
            if (_process == null) return;
            using var reader = _process.StandardError;
            while (!_process.HasExited)
            {
                string? line = await reader.ReadLineAsync();
                if (line == null) break;
                if (!string.IsNullOrWhiteSpace(line))
                {
                    LogBridge($"[PY-STDERR] {line}");
                }
            }
        }

        public async Task<JsonNode?> SendCommandAsync(string command, object? parameters = null, int timeoutMs = 8000)
        {
            if (_stdin == null || _process == null || _process.HasExited) return null;

            int id = Interlocked.Increment(ref _requestId);
            var cmdDict = new Dictionary<string, object?>
            {
                ["id"] = id,
                ["cmd"] = command
            };

            if (parameters != null)
            {
                foreach (var prop in parameters.GetType().GetProperties())
                {
                    cmdDict[prop.Name] = prop.GetValue(parameters);
                }
            }

            var tcs = new TaskCompletionSource<JsonNode?>();
            lock (_lock)
            {
                _pendingRequests[id] = tcs;
            }

            string jsonLine = JsonSerializer.Serialize(cmdDict);
            try
            {
                await _stdin.WriteLineAsync(jsonLine);
                await _stdin.FlushAsync();
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Failed to send command to Python bridge: {ex.Message}");
                lock (_lock) { _pendingRequests.Remove(id); }
                return null;
            }

            using var cts = new CancellationTokenSource(timeoutMs);
            cts.Token.Register(() =>
            {
                lock (_lock)
                {
                    if (_pendingRequests.Remove(id, out var pending))
                    {
                        pending.TrySetCanceled();
                    }
                }
            });

            try
            {
                return await tcs.Task;
            }
            catch (TaskCanceledException)
            {
                return null;
            }
        }

        public async Task<List<DeviceItem>> GetDevicesAsync()
        {
            try
            {
                var res = await SendCommandAsync("get_devices");
                if (res is JsonArray array)
                {
                    var list = new List<DeviceItem>();
                    foreach (var item in array)
                    {
                        if (item != null)
                        {
                            var dev = JsonSerializer.Deserialize<DeviceItem>(item.ToJsonString());
                            if (dev != null) list.Add(dev);
                        }
                    }
                    LogBridge($"Received {list.Count} real devices from Python bridge.");
                    return list;
                }
            }
            catch (Exception ex)
            {
                LogBridge($"Error fetching devices: {ex.Message}");
            }

            return new List<DeviceItem>();
        }

        public async Task<bool> StartScanAsync()
        {
            var res = await SendCommandAsync("start_scan");
            return res != null;
        }

        public async Task<bool> StopScanAsync()
        {
            var res = await SendCommandAsync("stop_scan");
            return res != null;
        }

        public async Task<DeviceItem?> BlockDeviceAsync(string mac)
        {
            var res = await SendCommandAsync("block_device", new { mac });
            if (res != null)
            {
                return JsonSerializer.Deserialize<DeviceItem>(res.ToJsonString());
            }
            return null;
        }

        public async Task<DeviceItem?> UnblockDeviceAsync(string mac)
        {
            var res = await SendCommandAsync("unblock_device", new { mac });
            if (res != null)
            {
                return JsonSerializer.Deserialize<DeviceItem>(res.ToJsonString());
            }
            return null;
        }

        public async Task<DeviceItem?> RenameDeviceAsync(string mac, string name)
        {
            var res = await SendCommandAsync("rename_device", new { mac, name });
            if (res != null)
            {
                return JsonSerializer.Deserialize<DeviceItem>(res.ToJsonString());
            }
            return null;
        }

        public void Dispose()
        {
            try
            {
                if (_stdin != null)
                {
                    _stdin.Close();
                    _stdin.Dispose();
                }
                if (_process != null && !_process.HasExited)
                {
                    _process.Kill();
                    _process.Dispose();
                }
            }
            catch { }
        }
    }
}

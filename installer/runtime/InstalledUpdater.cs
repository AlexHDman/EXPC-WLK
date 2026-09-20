using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Management;
using Microsoft.Win32;
using System.Text.RegularExpressions;
using System.Threading;

internal static class InstalledUpdater
{
    static readonly string[] Items = { "EXPC-WLK.exe", "runtime", "app", "updater" };
    static string log;

    static void Record(string message)
    {
        File.AppendAllText(log, DateTime.UtcNow.ToString("o") + " " + message + Environment.NewLine);
    }

    static void WaitExit(int pid)
    {
        if (pid <= 0) return;
        try
        {
            using (Process process = Process.GetProcessById(pid))
                if (!process.WaitForExit(60000)) throw new IOException("Application is still running.");
        }
        catch (ArgumentException) { }
    }

    static void StopTree(int pid)
    {
        using (var search = new ManagementObjectSearcher("SELECT ProcessId FROM Win32_Process WHERE ParentProcessId=" + pid))
        using (var children = search.Get())
            foreach (ManagementObject child in children) StopTree(Convert.ToInt32(child["ProcessId"]));
        try
        {
            using (Process process = Process.GetProcessById(pid))
            {
                process.Kill();
                process.WaitForExit(10000);
            }
        }
        catch (ArgumentException) { }
    }

    static void CheckTree(string path)
    {
        if (!File.Exists(path) && !Directory.Exists(path)) throw new IOException("Missing path: " + path);
        if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new IOException("Reparse points are not supported: " + path);
        if (Directory.Exists(path))
            foreach (string child in Directory.GetFileSystemEntries(path)) CheckTree(child);
    }

    static void CopyTree(string source, string destination)
    {
        CheckTree(source);
        if (File.Exists(source))
        {
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(source, destination, false);
            return;
        }
        Directory.CreateDirectory(destination);
        foreach (string directory in Directory.GetDirectories(source, "*", SearchOption.AllDirectories))
        {
            CheckTree(directory);
            Directory.CreateDirectory(destination + directory.Substring(source.Length));
        }
        foreach (string file in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            CheckTree(file);
            string target = destination + file.Substring(source.Length);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            File.Copy(file, target, false);
        }
    }

    static void MoveItem(string source, string destination)
    {
        if (Directory.Exists(source)) Directory.Move(source, destination);
        else File.Move(source, destination);
    }

    static void DeleteItem(string path)
    {
        if (Directory.Exists(path)) Directory.Delete(path, true);
        else if (File.Exists(path)) File.Delete(path);
    }

    static string Quote(string value)
    {
        if (value.IndexOf('\"') >= 0) throw new ArgumentException("Invalid quoted argument.");
        return "\"" + value + "\"";
    }

    static Process Launch(string root, string token, string receipt, bool testMode = false)
    {
        var info = new ProcessStartInfo(Path.Combine(root, "EXPC-WLK.exe"));
        info.WorkingDirectory = root;
        info.UseShellExecute = false;
        info.CreateNoWindow = true;
        if (token != null)
            info.Arguments = "--installed-update-token " + token +
                " --installed-update-receipt " + Quote(receipt);
        if (testMode) info.Arguments += " --test";
        return Process.Start(info);
    }

    static string ReadyContent(string token)
    {
        return "{\"format\":1,\"state\":\"ready\",\"token\":\"" + token + "\"}";
    }

    static bool HasValidReceipt(string receipt, string token)
    {
        try
        {
            if (!File.Exists(receipt)) return false;
            string content = File.ReadAllText(receipt).TrimEnd('\r', '\n');
            return content == ReadyContent(token);
        }
        catch (IOException) { return false; }
    }

    static void LaunchFromShell(string root)
    {
        var info = new ProcessStartInfo("explorer.exe", "\"" + Path.Combine(root, "EXPC-WLK.exe") + "\"");
        info.UseShellExecute = true;
        Process.Start(info);
    }

    static int Main(string[] args)
    {
        if (args.Length < 6 || args.Length > 10) return 2;
        string root = Path.GetFullPath(args[0]).TrimEnd(Path.DirectorySeparatorChar);
        string stage = Path.GetFullPath(args[1]).TrimEnd(Path.DirectorySeparatorChar);
        string receipt = Path.GetFullPath(args[2]);
        int launcherPid, appPid;
        if (!Int32.TryParse(args[3], out launcherPid) || !Int32.TryParse(args[4], out appPid)) return 2;
        string token = args[5];
        var options = new HashSet<string>(StringComparer.Ordinal);
        for (int index = 6; index < args.Length; index++)
            if (!options.Add(args[index])) return 2;
        foreach (string option in options)
            if (option != "--quiet" && option != "--simulate-failure" &&
                option != "--simulate-timeout" && option != "--simulate-malformed-receipt" &&
                option != "--keep-stage" && option != "--test-instance") return 2;
        bool quiet = options.Contains("--quiet");
        bool simulateFailure = options.Contains("--simulate-failure");
        bool simulateTimeout = options.Contains("--simulate-timeout");
        bool simulateMalformedReceipt = options.Contains("--simulate-malformed-receipt");
        bool keepStage = options.Contains("--keep-stage");
        bool testInstance = options.Contains("--test-instance");
        if (!Regex.IsMatch(token, "^[a-f0-9]{32}$")) return 2;

        string expectedReceipt = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "whisperkey", "installed-update-ready-" + token + ".json");
        if (!String.Equals(receipt, expectedReceipt, StringComparison.OrdinalIgnoreCase)) return 2;

        string programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!root.StartsWith(programFiles, StringComparison.OrdinalIgnoreCase)) return 2;
        foreach (string item in Items) CheckTree(Path.Combine(stage, item));
        if (Directory.Exists(Path.Combine(stage, "models"))) return 2;

        string parent = Path.GetDirectoryName(root);
        string backup = Path.Combine(parent, ".EXPC-WLK-installed-backup-" + token);
        string incoming = Path.Combine(parent, ".EXPC-WLK-installed-incoming-" + token);
        string failed = Path.Combine(parent, ".EXPC-WLK-installed-failed-" + token);
        log = Path.Combine(Path.GetDirectoryName(stage), "installed-update-" + token + ".log");
        Process started = null;
        bool movedOld = false, movedNew = false;

        using (Mutex gate = new Mutex(false, @"Local\WhisperKeyInstalledUpdate"))
        {
            bool acquired = false;
            try
            {
                try { acquired = gate.WaitOne(0); } catch (AbandonedMutexException) { acquired = true; }
                if (!acquired) throw new IOException("Another installed update is running.");
                WaitExit(launcherPid);
                WaitExit(appPid);
                if (Directory.Exists(backup) || Directory.Exists(incoming) || Directory.Exists(failed))
                    throw new IOException("Update recovery path already exists.");

                Directory.CreateDirectory(incoming);
                foreach (string item in Items)
                    CopyTree(Path.Combine(stage, item), Path.Combine(incoming, item));
                Directory.CreateDirectory(backup);
                foreach (string item in Items)
                    MoveItem(Path.Combine(root, item), Path.Combine(backup, item));
                movedOld = true;
                foreach (string item in Items)
                    MoveItem(Path.Combine(incoming, item), Path.Combine(root, item));
                movedNew = true;
                Directory.Delete(incoming);
                Record("Application payload replaced.");

                if (simulateFailure) throw new IOException("Simulated post-swap failure.");
                if (File.Exists(receipt)) File.Delete(receipt);
                if (simulateMalformedReceipt)
                    File.WriteAllText(receipt, "{malformed", System.Text.Encoding.ASCII);
                else if (!simulateTimeout)
                    started = Launch(root, token, receipt, testInstance);
                DateTime deadline = DateTime.UtcNow.AddSeconds(
                    simulateTimeout || simulateMalformedReceipt ? 2 : 180);
                bool ready = false;
                while (DateTime.UtcNow < deadline)
                {
                    if (HasValidReceipt(receipt, token))
                    {
                        ready = true;
                        break;
                    }
                    if (File.Exists(receipt))
                    {
                        try { File.Delete(receipt); Record("Ignored invalid Ready receipt."); }
                        catch (IOException) { }
                    }
                    Thread.Sleep(250);
                }
                if (!ready) throw new IOException("Updated application did not report a valid Ready receipt.");
                File.Delete(receipt);
                if (started != null && !started.HasExited) StopTree(started.Id);
                string releaseText = File.ReadAllText(Path.Combine(root, "updater", "config", "release.json"));
                Match releaseVersion = Regex.Match(releaseText, "\\\"version\\\"\\s*:\\s*\\\"([0-9]+\\.[0-9]+\\.[0-9]+)\\\"");
                if (!releaseVersion.Success) throw new IOException("Installed release version is invalid.");
                using (RegistryKey key = Registry.LocalMachine.OpenSubKey(
                    @"Software\Microsoft\Windows\CurrentVersion\Uninstall\{2E801B1E-38AA-47AE-A9CC-AC43AB1E60BA}_is1", true))
                    if (key != null) key.SetValue("DisplayVersion", releaseVersion.Groups[1].Value);
                Directory.Delete(backup, true);
                if (!keepStage) Directory.Delete(stage, true);
                if (!testInstance) LaunchFromShell(root);
                Record("Ready confirmed; transaction committed.");
                return 0;
            }
            catch (Exception error)
            {
                Record("Failure: " + error.Message);
                try
                {
                    if (started != null && !started.HasExited) StopTree(started.Id);
                    if (movedOld)
                    {
                        Directory.CreateDirectory(failed);
                        if (movedNew)
                            foreach (string item in Items)
                                MoveItem(Path.Combine(root, item), Path.Combine(failed, item));
                        foreach (string item in Items)
                            MoveItem(Path.Combine(backup, item), Path.Combine(root, item));
                        Directory.Delete(backup);
                        Directory.Delete(failed, true);
                        Record("Rollback complete.");
                        if (!quiet) Launch(root, null, null);
                    }
                }
                catch (Exception recovery) { Record("Manual recovery required: " + recovery.Message); }
                return 1;
            }
            finally
            {
                if (acquired) gate.ReleaseMutex();
                try { if (Directory.Exists(incoming)) Directory.Delete(incoming, true); } catch { }
            }
        }
    }
}

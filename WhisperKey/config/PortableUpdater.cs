using System;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Threading;
using System.Windows.Forms;

internal static class PortableUpdater
{
    static string log;
    static void Record(string message) { File.AppendAllText(log, DateTime.UtcNow.ToString("o") + " " + message + Environment.NewLine); }
    static void WaitExit(int pid) {
        try { using (Process p = Process.GetProcessById(pid)) {
            if (!p.WaitForExit(60000)) throw new IOException("Application is still running; update cancelled.");
        }} catch (ArgumentException) { }
    }
    static void CheckTree(string path) {
        if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) throw new IOException("Reparse points are not supported: " + path);
        if (Directory.Exists(path)) foreach (string child in Directory.GetFileSystemEntries(path)) CheckTree(child);
    }
    static bool Replaced(string relative) {
        string p = relative.Replace(Path.DirectorySeparatorChar, '/').ToLowerInvariant();
        return p == "expc-wlk.exe" || p == "whisperkey/app" || p.StartsWith("whisperkey/app/") ||
            p == "whisperkey/runtime" || p.StartsWith("whisperkey/runtime/");
    }
    static void Preserve(string source, string destination, string relative) {
        foreach (string entry in Directory.GetFileSystemEntries(source)) {
            string name = Path.GetFileName(entry);
            string rel = relative.Length == 0 ? name : relative + "/" + name;
            if (Replaced(rel)) continue;
            string target = Path.Combine(destination, name);
            // Model revision is managed independently from application releases.
            if (rel.Equals("WhisperKey/config/model-manifest.json", StringComparison.OrdinalIgnoreCase)) {
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                File.Copy(entry, target, true);
                continue;
            }
            if (Directory.Exists(entry)) {
                Directory.CreateDirectory(target); Preserve(entry, target, rel);
            } else if (!File.Exists(target)) File.Copy(entry, target);
        }
    }
    static Process Launch(string root, string token) {
        var info = new ProcessStartInfo(Path.Combine(root, "EXPC-WLK.exe"));
        info.WorkingDirectory = root; info.UseShellExecute = false;
        info.CreateNoWindow = true; info.WindowStyle = ProcessWindowStyle.Hidden;
        if (token != null) info.EnvironmentVariables["EXPC_WLK_UPDATE_TOKEN"] = token;
        else info.EnvironmentVariables.Remove("EXPC_WLK_UPDATE_TOKEN");
        return Process.Start(info);
    }
    static void StopTree(int pid) {
        using (var search = new ManagementObjectSearcher("SELECT ProcessId FROM Win32_Process WHERE ParentProcessId=" + pid))
        using (var children = search.Get()) foreach (ManagementObject child in children) StopTree(Convert.ToInt32(child["ProcessId"]));
        try { using (Process p = Process.GetProcessById(pid)) { p.Kill(); p.WaitForExit(10000); } }
        catch (ArgumentException) { }
    }
    [STAThread] static int Main(string[] args) {
        if (args.Length != 5 && !(args.Length == 6 && args[5] == "--quiet")) return 2;
        string root = Path.GetFullPath(args[0]).TrimEnd(Path.DirectorySeparatorChar);
        string stage = Path.GetFullPath(args[1]);
        string work = Path.GetDirectoryName(stage);
        string token = args[4];
        string previous = root + ".previous-" + token;
        string failed = root + ".failed-" + token;
        string receipt = Path.Combine(root, "WhisperKey", "logs", "update-ready-" + token);
        if (!System.Text.RegularExpressions.Regex.IsMatch(token, "^[a-f0-9]{32}$") ||
            !String.Equals(Path.GetDirectoryName(work), Path.GetDirectoryName(root), StringComparison.OrdinalIgnoreCase) ||
            !Path.GetFileName(work).StartsWith(".EXPC-WLK-update-", StringComparison.Ordinal) || Path.GetFileName(stage) != "stage") return 2;
        log = Path.Combine(work, "transaction.log");
        Process started = null;
        bool oldMoved = false, newMoved = false, closed = false;
        using (Mutex gate = new Mutex(false, @"Local\WhisperKeyPortableUpdate")) {
            bool acquired = false;
            try {
                try { acquired = gate.WaitOne(0); } catch (AbandonedMutexException) { acquired = true; }
                if (!acquired) throw new IOException("Another update is running.");
                WaitExit(Int32.Parse(args[2])); WaitExit(Int32.Parse(args[3])); closed = true;
                CheckTree(root); CheckTree(stage);
                if (Directory.Exists(previous) || Directory.Exists(failed)) throw new IOException("Recovery path already exists.");
                Record("Preparing preserved files; current installation unchanged.");
                Preserve(root, stage, "");
                Record("Stage complete. Previous=" + previous);
                Directory.Move(root, previous); oldMoved = true;
                Directory.Move(stage, root); newMoved = true;
                Record("Swapped complete installation.");
                started = Launch(root, token);
                DateTime deadline = DateTime.UtcNow.AddSeconds(120);
                while (DateTime.UtcNow < deadline && !File.Exists(receipt) && !started.HasExited) Thread.Sleep(250);
                if (!File.Exists(receipt)) throw new IOException("Updated application did not report Ready.");
                Record("Ready confirmed; update successful.");
                // Delete only the exact transaction snapshot after successful startup.
                try { Directory.Delete(previous, true); } catch (Exception ex) { Record("Snapshot cleanup pending: " + ex.Message); }
                File.Delete(receipt);
                return 0;
            } catch (Exception ex) {
                Record("Failure: " + ex.Message);
                try {
                    if (started != null && !started.HasExited) StopTree(started.Id);
                    if (oldMoved) {
                        if (!acquired) { try { gate.WaitOne(); } catch (AbandonedMutexException) { } acquired = true; }
                        if (newMoved) Directory.Move(root, failed); // Retain failed-version logs for diagnosis.
                        Directory.Move(previous, root);
                        Record("Rollback complete.");
                        gate.ReleaseMutex(); acquired = false;
                        Launch(root, null);
                    } else if (closed && Directory.Exists(root)) {
                        if (acquired) { gate.ReleaseMutex(); acquired = false; }
                        Launch(root, null);
                    }
                } catch (Exception recovery) { Record("Manual recovery required: " + recovery.Message + "; previous=" + previous); }
                if (args.Length == 5) MessageBox.Show("Update failed / Обновление не выполнено.\n" + ex.Message + "\n" + log, "EXPC-WLK", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return 1;
            } finally { if (acquired) gate.ReleaseMutex(); }
        }
    }
}

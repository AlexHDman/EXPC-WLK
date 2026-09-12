using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("EXPC-WLK")]
[assembly: AssemblyProduct("EXPC-WLK")]
[assembly: AssemblyDescription("EXPC-WLK portable launcher")]
// AssemblyVersion is generated from release.json by build_launchers.ps1.

internal static class PortableLauncher
{
    private const string Product = "EXPC-WLK";
    private const string AutostartName = "EXPC-WLK";

    [STAThread]
    private static int Main(string[] args)
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string logDir = Path.Combine(root, "WhisperKey", "logs");
        try
        {
            if (args.Length >= 1 && (args[0] == "--enable-autostart" || args[0] == "--disable-autostart"))
            {
                using (RegistryKey key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run"))
                {
                    if (args[0] == "--enable-autostart")
                        key.SetValue(AutostartName, "\"" + Application.ExecutablePath + "\"");
                    else
                        key.DeleteValue(AutostartName, false);
                }
                using (RegistryKey approval = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run", true))
                {
                    if (approval != null) approval.DeleteValue(AutostartName, false);
                }
                if (args.Length < 2 || args[1] != "--quiet")
                    MessageBox.Show(args[0] == "--enable-autostart" ? "EXPC-WLK per-user autostart enabled. Disable any old WhisperKey Startup shortcut to avoid starting two installations." : "EXPC-WLK autostart disabled.", Product);
                return 0;
            }
            if (String.IsNullOrEmpty(Environment.GetEnvironmentVariable("EXPC_WLK_UPDATE_TOKEN")))
            using (Mutex updateGate = new Mutex(false, @"Local\WhisperKeyPortableUpdate"))
            {
                bool entered = false;
                try { try { entered = updateGate.WaitOne(0); } catch (AbandonedMutexException) { entered = true; }
                    if (!entered) { MessageBox.Show("Update in progress / Выполняется обновление", Product); return 0; }
                } finally { if (entered) updateGate.ReleaseMutex(); }
            }
            bool created;
            // Keep existing mutex names for compatibility with prior instances.
            using (Mutex guard = new Mutex(true, @"Local\WhisperKeyPortableLauncher", out created))
            {
                bool existingApp = false;
                try { using (Mutex app = Mutex.OpenExisting("WhisperKeyLocal_SingleInstance")) { existingApp = true; } }
                catch (WaitHandleCannotBeOpenedException) { }
                if (!created || existingApp)
                {
                    Directory.CreateDirectory(logDir);
                    File.AppendAllText(Path.Combine(logDir, "launcher.log"), DateTime.Now.ToString("o") + " ALREADY_RUNNING\n");
                    MessageBox.Show("EXPC-WLK is already running. Use its tray icon. Exit the existing instance before starting another copy.", Product, MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return 0;
                }
                string python = Path.Combine(root, "WhisperKey", "runtime", "pythonw.exe");
                string boot = Path.Combine(root, "WhisperKey", "app", "portable_boot.py");
                if (!File.Exists(python) || !File.Exists(boot))
                    throw new FileNotFoundException("Portable runtime is missing. Copy the entire EXPC-WLK folder, including WhisperKey.");
                ProcessStartInfo info = new ProcessStartInfo(python, "-I \"" + boot + "\"");
                info.WorkingDirectory = Path.Combine(root, "WhisperKey");
                info.UseShellExecute = false;
                info.CreateNoWindow = true;
                info.WindowStyle = ProcessWindowStyle.Hidden;
                info.EnvironmentVariables.Remove("PYTHONHOME");
                info.EnvironmentVariables.Remove("PYTHONPATH");
                using (EventWaitHandle restart = new EventWaitHandle(false, EventResetMode.ManualReset, @"Local\WhisperKeyPortableRestart"))
                {
                    while (true)
                    {
                        restart.Reset();
                        using (Process child = Process.Start(info))
                        {
                            child.WaitForExit();
                            if (!restart.WaitOne(0)) return child.ExitCode;
                        }
                    }
                }
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, Product, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}

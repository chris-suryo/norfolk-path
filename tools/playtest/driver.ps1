# Native game driver: window focus, scancode input, client-area screenshots.
# Dot-source this file, then use: Start-Game, Focus-Game, Tap, Hold-Keys, Shot, Stop-Game

Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class GameDrv {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, IntPtr pid);
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr hWnd, ref POINT lpPoint);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", SetLastError=true)] public static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();

    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }

    [StructLayout(LayoutKind.Sequential)]
    public struct KEYBDINPUT { public ushort wVk; public ushort wScan; public uint dwFlags; public uint time; public IntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Explicit)]
    public struct INPUTUNION { [FieldOffset(0)] public KEYBDINPUT ki; [FieldOffset(0)] public long pad1; [FieldOffset(8)] public long pad2; [FieldOffset(16)] public long pad3; }
    [StructLayout(LayoutKind.Sequential)]
    public struct INPUT { public uint type; public INPUTUNION u; }

    public const uint INPUT_KEYBOARD = 1;
    public const uint KEYEVENTF_SCANCODE = 0x0008;
    public const uint KEYEVENTF_KEYUP = 0x0002;
    public const uint KEYEVENTF_EXTENDEDKEY = 0x0001;

    public static void Key(ushort scan, bool extended, bool up) {
        INPUT[] inp = new INPUT[1];
        inp[0].type = INPUT_KEYBOARD;
        inp[0].u.ki.wVk = 0;
        inp[0].u.ki.wScan = scan;
        inp[0].u.ki.dwFlags = KEYEVENTF_SCANCODE | (extended ? KEYEVENTF_EXTENDEDKEY : 0) | (up ? KEYEVENTF_KEYUP : 0);
        SendInput(1, inp, Marshal.SizeOf(typeof(INPUT)));
    }
}
"@

[void][GameDrv]::SetProcessDPIAware()

# key name -> vk, scancode, extended
$script:KeyMap = @{
    'W' = @(0x57, 0x11, $false); 'A' = @(0x41, 0x1E, $false); 'S' = @(0x53, 0x1F, $false); 'D' = @(0x44, 0x20, $false)
    'C' = @(0x43, 0x2E, $false); 'Space' = @(0x20, 0x39, $false); 'Enter' = @(0x0D, 0x1C, $false); 'Esc' = @(0x1B, 0x01, $false)
    'Up' = @(0x26, 0x48, $true); 'Down' = @(0x28, 0x50, $true); 'Left' = @(0x25, 0x4B, $true); 'Right' = @(0x27, 0x4D, $true)
    'Slash' = @(0xBF, 0x35, $false); 'Period' = @(0xBE, 0x34, $false)
}

$script:ShotDir = 'E:\code\norfolk-path\docs\playtest\round-1'

function Get-GameWindow {
    $p = Get-Process -Name 'Godot_v4.7-stable_win64', 'Godot_v4.7-stable_win64_console' -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -like '*norfolk*' } | Select-Object -First 1
    if ($null -eq $p) { throw 'game window not found' }
    return $p.MainWindowHandle
}

function Start-Game {
    $exe = 'C:\Users\harim\Documents\Programs\Godot_v4.7-stable_win64.exe\Godot_v4.7-stable_win64.exe'
    Start-Process -FilePath $exe -ArgumentList '--path', 'E:\code\norfolk-path' | Out-Null
    Start-Sleep -Seconds 6
    [void](Use-GameWindow)
}

function Stop-Game {
    Get-Process -Name 'Godot_v4.7-stable_win64' -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -like '*norfolk*' } | Stop-Process -Force
}

function Focus-Game {
    $h = Get-GameWindow
    [void][GameDrv]::ShowWindow($h, 9)
    # keep the game above everything so captures are never occluded
    [void][GameDrv]::SetWindowPos($h, [IntPtr](-1), 0, 0, 0, 0, 0x0003) # HWND_TOPMOST, NOSIZE|NOMOVE
    for ($i = 0; $i -lt 5; $i++) {
        $fg = [GameDrv]::GetForegroundWindow()
        if ($fg -eq $h) { break }
        $fgThread = [GameDrv]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
        $me = [GameDrv]::GetCurrentThreadId()
        [void][GameDrv]::AttachThreadInput($me, $fgThread, $true)
        [void][GameDrv]::SetForegroundWindow($h)
        [void][GameDrv]::AttachThreadInput($me, $fgThread, $false)
        Start-Sleep -Milliseconds 200
    }
    if ([GameDrv]::GetForegroundWindow() -ne $h) { throw 'could not focus game window' }
    Start-Sleep -Milliseconds 200
}

function Assert-GameFocused {
    $h = Get-GameWindow
    if ([GameDrv]::GetForegroundWindow() -ne $h) { Focus-Game }
}

Add-Type @"
using System; using System.Runtime.InteropServices;
public static class PMsg { [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam); }
"@ -ErrorAction SilentlyContinue

$script:GameHwnd = [IntPtr]::Zero
function Use-GameWindow { $script:GameHwnd = Get-GameWindow; return $script:GameHwnd }

function Key-Down([string]$k) {
    if ($script:GameHwnd -eq [IntPtr]::Zero) { [void](Use-GameWindow) }
    $m = $script:KeyMap[$k]
    $ext = 0; if ($m[2]) { $ext = 1 }
    $lp = [IntPtr]([long](1 -bor ($m[1] -shl 16) -bor ($ext -shl 24)))
    [void][PMsg]::PostMessage($script:GameHwnd, 0x0100, [IntPtr]([long]$m[0]), $lp)
}
function Key-Up([string]$k) {
    if ($script:GameHwnd -eq [IntPtr]::Zero) { [void](Use-GameWindow) }
    $m = $script:KeyMap[$k]
    $ext = 0; if ($m[2]) { $ext = 1 }
    $lp = [IntPtr]([long](1 -bor ($m[1] -shl 16) -bor ($ext -shl 24) -bor 0xC0000000))
    [void][PMsg]::PostMessage($script:GameHwnd, 0x0101, [IntPtr]([long]$m[0]), $lp)
}

function Tap([string]$k, [int]$ms = 60) {
    Key-Down $k; Start-Sleep -Milliseconds $ms; Key-Up $k
    Start-Sleep -Milliseconds 140
}

# hold several keys at once for a duration
function Hold-Keys([string[]]$keys, [int]$ms) {
    foreach ($k in $keys) { Key-Down $k }
    Start-Sleep -Milliseconds $ms
    foreach ($k in $keys) { Key-Up $k }
    Start-Sleep -Milliseconds 100
}

function Shot([string]$name) {
    $h = Get-GameWindow
    $wr = New-Object GameDrv+RECT
    [void][GameDrv]::GetWindowRect($h, [ref]$wr)
    $w = $wr.Right - $wr.Left; $ht = $wr.Bottom - $wr.Top
    $bmp = New-Object System.Drawing.Bitmap($w, $ht)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    # PW_RENDERFULLCONTENT (2) captures GPU-rendered content
    [void][GameDrv]::PrintWindow($h, $hdc, 2)
    $g.ReleaseHdc($hdc)
    $g.Dispose()
    # crop title bar / borders: client rect offset within window
    $cr = New-Object GameDrv+RECT
    [void][GameDrv]::GetClientRect($h, [ref]$cr)
    $pt = New-Object GameDrv+POINT; $pt.X = 0; $pt.Y = 0
    [void][GameDrv]::ClientToScreen($h, [ref]$pt)
    $offX = $pt.X - $wr.Left; $offY = $pt.Y - $wr.Top
    $cw = $cr.Right; $chh = $cr.Bottom
    if ($offX -ge 0 -and $offY -ge 0 -and ($offX + $cw) -le $w -and ($offY + $chh) -le $ht -and $cw -gt 0) {
        $crop = $bmp.Clone((New-Object System.Drawing.Rectangle($offX, $offY, $cw, $chh)), $bmp.PixelFormat)
        $bmp.Dispose(); $bmp = $crop
    }
    $path = Join-Path $script:ShotDir $name
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $dims = "$($bmp.Width) x $($bmp.Height)"
    $bmp.Dispose()
    return "$name ($dims)"
}

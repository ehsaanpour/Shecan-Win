'''# DNS Toggler for Windows

A simple Python application with a Tkinter GUI to quickly toggle DNS settings on your active Windows network interface.

## Features

-   **One-Click Toggle**: Easily switch your IPv4 DNS settings on or off.
-   **Specific DNS Servers**: Uses the following DNS servers when turned "ON":
    -   Primary: `178.22.122.100`
    -   Secondary: `185.51.200.2`
-   **Automatic Clearing**: When turned "OFF", DNS settings are reverted to be obtained automatically (DHCP).
-   **Active Interface Detection**: Attempts to automatically find your active network interface (e.g., "Ethernet" or "Wi-Fi").
-   **Administrator Check**: Notifies if not run with administrator privileges, as these are required to change network settings.
-   **Initial State Detection**: Checks the current DNS state on startup and sets the button accordingly.

## Prerequisites

-   Windows Operating System
-   Python 3.x installed and added to PATH.

## How to Run

1.  **Download**: Get the `dns_toggler.py` file.
2.  **Administrator Privileges**: You **must** run this script as an administrator.
    -   Right-click on the `dns_toggler.py` file and select "Run as administrator".
    -   Alternatively, open Command Prompt or PowerShell as an administrator, navigate to the directory containing the script, and run it using `python dns_toggler.py`.
3.  **Usage**:
    -   The application window will show the current DNS status.
    -   Click the button to toggle the DNS settings ON or OFF.
    -   "Status: DNS ON" means the custom DNS servers are active.
    -   "Status: DNS OFF" means DNS settings are being obtained automatically via DHCP.

## Files

-   `dns_toggler.py`: The main Python application script.
-   `README.md`: This file.
-   `requirements.txt`: Lists dependencies (though this app only uses standard Python libraries).

## Notes

-   The application uses `netsh` commands internally to modify network settings.
-   If you have multiple active network interfaces, the script attempts to choose the primary one (typically the one with a default gateway). If it fails to find an active interface or the correct one, DNS changes might not apply as expected.
-   The `creationflags=subprocess.CREATE_NO_WINDOW` flag is used with `subprocess.run` to prevent terminal windows from flashing open when `netsh` or `powershell` commands are executed.
''' 
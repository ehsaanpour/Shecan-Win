import tkinter as tk
from tkinter import ttk # Import ttk
import subprocess
import ctypes
import sys
import webbrowser # For opening URL

# --- Persian Texts ---
persian_texts = {
    "window_title": "شکن نسخه ویندوزی",
    "status_label_prefix": "وضعیت شکن:",
    "status_unknown": "نامشخص",
    "status_dns_on": "شکن روشن",
    "status_dns_off": "شکن خاموش",
    "button_turn_on": "شکن را روشن کنید",
    "button_turn_off": "شکن را خاموش کنید",
    "error_admin_required": "خطا: برنامه باید با دسترسی ادمین اجرا شود!",
    "error_no_active_interface": "خطا: رابط شبکه فعال پیدا نشد.",
    "error_powershell_not_found": "خطا: پاورشل پیدا نشد.",
    "error_set_dns_failed": "خطا: تنظیم DNS ناموفق بود.",
    "error_netsh_not_found": "خطا: دستور netsh پیدا نشد.",
    "error_clear_dns_failed": "خطا: پاک کردن DNS ناموفق بود.",
    "status_no_active_interface_found": "وضعیت: رابط شبکه فعال پیدا نشد.",
    "error_toggle_no_active_interface": "خطا: رابط شبکه فعال برای تغییر وضعیت وجود ندارد.",
    "guidance_text": "این برنامه توسط احسان احسانپور توسعه یافته است",
    "app_error_title": "خطای برنامه",
    "app_error_unexpected": "یک خطای پیش بینی نشده رخ داده است:",
    "main_exception_tclerror_messagebox": "خطای اصلی: TclError هنگام نمایش پیام خطا. ممکن است Tkinter قابل استفاده نباشد.",
    "initial_button_text": "بررسی وضعیت..." # Initial button text before state is known
}
# --- End Persian Texts ---

class AnimatedToggle(tk.Canvas):
    def __init__(self, parent, command=None, **kwargs):
        # Calculate width and height based on desired toggle size
        self.width = 60
        self.height = 30
        self.knob_radius = (self.height - 8) / 2 # Adjusted padding for knob
        self.padding = 4

        super().__init__(parent, width=self.width, height=self.height, relief="flat", highlightthickness=0, **kwargs)
        self.command = command
        self.is_on = False

        # Modern Colors
        self.track_on_color = "#28A745"  # Vibrant Green
        self.track_off_color = "#CCCCCC" # Light Gray
        self.knob_color = "#FFFFFF"
        self.border_color = "#6c757d" # Darker gray for better contrast

        self.bind("<Button-1>", self._on_click)

        self.track = self._draw_rounded_rect(self.padding, self.padding, 
                                             self.width - self.padding, self.height - self.padding, 
                                             radius=self.knob_radius + self.padding / 2,
                                             fill=self.track_off_color, outline="")
        
        self.knob_x = self.padding + self.knob_radius
        self.knob = self.create_oval(self.knob_x - self.knob_radius, self.padding, 
                                     self.knob_x + self.knob_radius, self.height - self.padding,
                                     fill=self.knob_color, outline=self.border_color, width=1) # Changed width to 1
        self.animation_steps = 8
        self.animation_delay = 12 # milliseconds

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draws a rounded rectangle on the canvas."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        # smooth=True is kept for the track, as jagged edges are usually less desirable
        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_click(self, event):
        if self.cget("state") == tk.DISABLED:
            return
        # Command is called by DNSToggler.toggle_dns which then calls update_ui_for_state -> toggle.set_state
        # Here we just trigger the command; the parent will manage the state change and animation
        if self.command:
            self.command()

    def _animate_knob(self, target_x):
        current_x1, _, current_x2, _ = self.coords(self.knob)
        current_knob_center_x = (current_x1 + current_x2) / 2

        dx = (target_x - current_knob_center_x) / self.animation_steps

        def _step(step_count):
            if step_count <= self.animation_steps:
                self.move(self.knob, dx, 0)
                self.after(self.animation_delay, lambda: _step(step_count + 1))
            else:
                final_x1 = target_x - self.knob_radius
                final_y1 = self.padding
                final_x2 = target_x + self.knob_radius
                final_y2 = self.height - self.padding
                self.coords(self.knob, final_x1, final_y1, final_x2, final_y2)
                # self.is_on state is now managed by DNSToggler via set_state
                # self.update_appearance() # Appearance updated by set_state
        _step(1)

    def set_state(self, is_on, animate=False):
        target_is_on = bool(is_on)
        if self.is_on == target_is_on and not animate: # Allow re-animation if animate is true
            return

        self.is_on = target_is_on # Update internal state first
        self.update_appearance() # Update track color immediately

        target_x = (self.width - self.padding - self.knob_radius) if self.is_on else (self.padding + self.knob_radius)
        if animate:
            self._animate_knob(target_x)
        else:
            # Snap knob to position
            x1 = target_x - self.knob_radius
            y1 = self.padding
            x2 = target_x + self.knob_radius
            y2 = self.height - self.padding
            self.coords(self.knob, x1, y1, x2, y2)

    def update_appearance(self):
        if self.is_on:
            self.itemconfig(self.track, fill=self.track_on_color)
        else:
            self.itemconfig(self.track, fill=self.track_off_color)

class DNSToggler:
    def __init__(self, master):
        print("DNSToggler __init__: Start")
        self.master = master
        master.title(persian_texts["window_title"])
        master.geometry("420x280") # Slightly adjusted size
        # master.configure(bg="#ECECEC") # Will be covered by gradient canvas

        # Font Definitions
        self.font_family = ("Vazir", "Segoe UI", "Arial", "sans-serif") # Prioritize Vazir
        self.font_normal = (self.font_family[0], 11)
        self.font_small = (self.font_family[0], 9)
        self.font_status = (self.font_family[0], 12, "bold")

        # Gradient Background Canvas
        self.grad_canvas = tk.Canvas(master, highlightthickness=0)
        self.grad_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # New Blue to Green Gradient
        self.gradient_start_color = "#007bff"  # Bright Blue (Bootstrap primary)
        self.gradient_end_color = "#28a745"    # Bright Green (Bootstrap success)
        master.bind("<Configure>", self._draw_gradient_background)
        self._draw_gradient_background() # Initial draw

        # Style configuration for ttk widgets
        style = ttk.Style()
        style.theme_use('clam')
        # Configure widgets to use a base color that matches the start of the gradient
        # Forcing background color for TFrame for better blending
        style.configure("TFrame", background=self.gradient_start_color)
        style.configure("TLabel", font=self.font_normal, background=self.gradient_start_color)
        style.configure("Url.TLabel", font=self.font_small, foreground="#FFFFFF", background=self.gradient_start_color) # White on blue
        style.map("Url.TLabel", foreground=[('active', "#DDDDDD")]) # Lighter white on hover

        self.dns_on = False
        self.dns_servers = ["178.22.122.100", "185.51.200.2"]
        self.pulse_animation_id = None

        # Main frame (transparent to show gradient)
        main_frame = ttk.Frame(master, style="TFrame", padding="20 20 20 20")
        # Need to make TFrame background transparent or match gradient.
        # Forcing style for TFrame as well to make it blend better.
        style.configure("TFrame", background=self.gradient_start_color) # Match gradient top
        main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER) # Center the main content

        # Status display (Light + Text)
        status_display_frame = ttk.Frame(main_frame, style="TFrame")
        status_display_frame.pack(pady=(0, 25), fill=tk.X)
        status_display_frame.columnconfigure(1, weight=1) # Allow text to expand

        self.indicator_canvas = tk.Canvas(status_display_frame, width=26, height=26, highlightthickness=0, bg=self.gradient_start_color)
        self.indicator_canvas.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.indicator_light_id = self.indicator_canvas.create_oval(3, 3, 23, 23, fill="gray", outline="#FFFFFF", width=1.5) # White outline for light

        self.status_label = ttk.Label(status_display_frame, text=f"{persian_texts['status_label_prefix']} {persian_texts['status_unknown']}", font=self.font_status, style="TLabel")
        self.status_label.grid(row=0, column=1, sticky="w")

        # Animated Toggle Switch
        self.toggle_switch = AnimatedToggle(main_frame, command=self.toggle_dns, bg=self.gradient_start_color)
        self.toggle_switch.pack(pady=20)

        # Guidance Text Label (Clickable)
        self.guidance_label = ttk.Label(main_frame, text=persian_texts["guidance_text"], style="Url.TLabel", cursor="hand2")
        self.guidance_label.pack(pady=(20, 0))
        self.guidance_label.bind("<Button-1>", lambda e: self.open_developer_url())
        # Adjusting hover font for Url.TLabel for clarity with Vazir
        hover_font_small_underline = (self.font_family[0], 9, "underline")
        self.guidance_label.bind("<Enter>", lambda e: self.guidance_label.config(font=hover_font_small_underline))
        self.guidance_label.bind("<Leave>", lambda e: self.guidance_label.config(font=self.font_small))
        
        if not self.is_admin():
            self.update_ui_for_state(admin_error=True)
            if self.toggle_switch: self.toggle_switch.config(state=tk.DISABLED)
        else:
            self.toggle_switch.set_state(False, animate=False)
            self.check_initial_dns_state()
        print("DNSToggler __init__: End")

    def _draw_gradient_background(self, event=None):
        self.grad_canvas.delete("gradient")
        width = self.grad_canvas.winfo_width()
        height = self.grad_canvas.winfo_height()
        if width <= 1 or height <= 1: # Check for valid dimensions
            self.master.after(50, self._draw_gradient_background)
            return
        
        r1, g1, b1 = self.master.winfo_rgb(self.gradient_start_color)
        r2, g2, b2 = self.master.winfo_rgb(self.gradient_end_color)
        r1,g1,b1 = r1//256, g1//256, b1//256
        r2,g2,b2 = r2//256, g2//256, b2//256

        for i in range(height):
            # Calculate interpolated color components
            # Ensure i / (height -1) or similar if height can be 1 and i range is 0 to height-1
            # If height is the number of lines, then i/height is fine for 0 to height-1 iterations
            ratio = i / height 
            nr = int(r1 * (1 - ratio) + r2 * ratio)
            ng = int(g1 * (1 - ratio) + g2 * ratio)
            nb = int(b1 * (1 - ratio) + b2 * ratio)
            color = f"#{nr:02x}{ng:02x}{nb:02x}"
            self.grad_canvas.create_line(0, i, width, i, fill=color, tags="gradient")

    def _start_pulse_animation(self, is_on_state):
        if self.pulse_animation_id:
            self.master.after_cancel(self.pulse_animation_id)
            self.pulse_animation_id = None

        initial_radius = 10
        max_radius_expansion = 1.5 # Reduced pulse expansion for subtlety
        current_radius_expansion = [0]
        direction = [1]
        base_color = "#20C997" if is_on_state else "#DC3545" # Minty Green for On, Bootstrap Red for Off
        outline_color = "#FFFFFF" # White outline for pulsing light

        def pulse():
            r_exp = current_radius_expansion[0]
            # Simple brightness modulation (could be more sophisticated)
            intensity_factor = 1.0 - (r_exp / (max_radius_expansion * 5)) 
            r_base, g_base, b_base = self.master.winfo_rgb(base_color)
            r_pulse = int(r_base/256 * intensity_factor)
            g_pulse = int(g_base/256 * intensity_factor)
            b_pulse = int(b_base/256 * intensity_factor)
            pulse_color = f"#{max(0, min(255, r_pulse)):02x}{max(0, min(255, g_pulse)):02x}{max(0, min(255, b_pulse)):02x}"

            center_x, center_y = 13, 13
            current_r = initial_radius + r_exp
            self.indicator_canvas.delete(self.indicator_light_id)
            self.indicator_light_id = self.indicator_canvas.create_oval(
                center_x - current_r, center_y - current_r,
                center_x + current_r, center_y + current_r,
                fill=pulse_color, outline=outline_color, width=1 # Thin white outline
            )
            
            current_radius_expansion[0] += 0.15 * direction[0] # Slower pulse
            if current_radius_expansion[0] >= max_radius_expansion:
                direction[0] = -1
            elif current_radius_expansion[0] <= 0:
                direction[0] = 1
            
            self.pulse_animation_id = self.master.after(80, pulse) # Slower pulse frequency

        pulse()

    def _stop_pulse_animation(self, final_color="gray"):
        if self.pulse_animation_id:
            self.master.after_cancel(self.pulse_animation_id)
            self.pulse_animation_id = None
        self.indicator_canvas.delete(self.indicator_light_id)
        # Consistent outline for static light
        self.indicator_light_id = self.indicator_canvas.create_oval(3, 3, 23, 23, fill=final_color, outline="#FFFFFF", width=1.5)

    def update_ui_for_state(self, status_key=None, error_key=None, admin_error=False, interface_error=False, custom_message=None):
        current_status_text = ""
        indicator_color_static = "#adb5bd" # Default static to a neutral gray
        start_pulse_for_state = None
        new_dns_state_for_toggle = self.dns_on

        if admin_error:
            current_status_text = persian_texts["error_admin_required"]
            indicator_color_static = "#ffc107"  # Amber (Bootstrap warning)
            self._stop_pulse_animation(final_color=indicator_color_static)
        elif interface_error:
            current_status_text = persian_texts["status_no_active_interface_found"]
            indicator_color_static = "#6c757d"  # Darker Gray (Bootstrap secondary)
            self._stop_pulse_animation(final_color=indicator_color_static)
        elif error_key:
            current_status_text = persian_texts.get(error_key, error_key)
            indicator_color_static = "#dc3545"  # Red (Bootstrap danger)
            self._stop_pulse_animation(final_color=indicator_color_static)
        elif custom_message:
            current_status_text = custom_message
            indicator_color_static = "#6c757d"
            self._stop_pulse_animation(final_color=indicator_color_static)
        elif status_key:
            current_status_text = f"{persian_texts['status_label_prefix']} {persian_texts.get(status_key, status_key)}"
            if status_key == "status_dns_on":
                new_dns_state_for_toggle = True
                start_pulse_for_state = True 
            else:
                new_dns_state_for_toggle = False
                if status_key == "status_dns_off":
                    start_pulse_for_state = False
                else: # status_unknown
                    indicator_color_static = "#adb5bd" # Bootstrap light gray
                    self._stop_pulse_animation(final_color=indicator_color_static)
        
        self.status_label.config(text=current_status_text)
        
        if start_pulse_for_state is not None:
            self._start_pulse_animation(is_on_state=start_pulse_for_state)
        else:
            self.indicator_canvas.itemconfig(self.indicator_light_id, fill=indicator_color_static, outline="#FFFFFF")

        # Update the toggle switch visual state and internal class dns_on state
        self.dns_on = new_dns_state_for_toggle
        if self.toggle_switch and self.toggle_switch.is_on != self.dns_on:
            # Animate only if the change is programmatic (not from user clicking the toggle itself)
            # The click on toggle itself triggers animation, then calls toggle_dns, which calls this.
            # We want to avoid double animation or fighting animations.
            # For initial state or programmatic changes (like set_dns/clear_dns succeeding):
            self.toggle_switch.set_state(self.dns_on, animate=True) 

    def open_developer_url(self):
        try:
            webbrowser.open_new_tab("https://ehsaanpour.github.io/Me/index.html")
        except Exception as e:
            print(f"Error opening URL: {e}")

    def is_admin(self):
        print("is_admin: Checking...")
        try:
            result = ctypes.windll.shell32.IsUserAnAdmin()
            print(f"is_admin: Result = {result}")
            return result
        except Exception as e:
            print(f"is_admin: Error - {e}")
            return False

    def rerun_as_admin(self):
        print("rerun_as_admin: Attempting to rerun as admin")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        self.master.destroy()
        sys.exit()

    def get_active_interface_name(self):
        print("get_active_interface_name: Start")
        try:
            print("get_active_interface_name: Trying Get-NetIPConfiguration...")
            result = subprocess.run(["powershell", "-Command", "Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up' } | Select-Object -First 1 -ExpandProperty InterfaceAlias"], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            interface_name = result.stdout.strip()
            print(f"get_active_interface_name: Get-NetIPConfiguration result - '{interface_name}'")
            if not interface_name:
                print("get_active_interface_name: No interface from Get-NetIPConfiguration. Trying Get-NetAdapter...")
                result = subprocess.run(["powershell", "-Command", "(Get-NetAdapter | Where-Object {($_.Name -like 'Ethernet*' -or $_.Name -like 'Wi-Fi*') -and $_.Status -eq 'Up'} | Select-Object -First 1).Name"], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                interface_name = result.stdout.strip()
                print(f"get_active_interface_name: Get-NetAdapter result - '{interface_name}'")
            if interface_name:
                if ":" in interface_name:
                    interface_name = interface_name.split(":")[0].strip()
                    print(f"get_active_interface_name: Cleaned interface name - '{interface_name}'")
                print(f"get_active_interface_name: Returning '{interface_name}'")
                return interface_name
            else:
                print("get_active_interface_name: No interface found after all attempts.")
                self.update_ui_for_state(error_key="error_no_active_interface")
        except subprocess.CalledProcessError as e:
            print(f"get_active_interface_name: subprocess.CalledProcessError - {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
            self.update_ui_for_state(error_key="error_no_active_interface")
        except FileNotFoundError as e:
            print(f"get_active_interface_name: FileNotFoundError - {e} (likely PowerShell)")
            self.update_ui_for_state(custom_message=persian_texts["error_powershell_not_found"])
        except Exception as e:
            print(f"get_active_interface_name: Generic error - {e}")
            self.update_ui_for_state(custom_message=str(e))
        print("get_active_interface_name: End, returning None")
        return None

    def set_dns(self, interface_name):
        print(f"set_dns: Start for interface '{interface_name}'")
        try:
            cmd_set_primary = f'netsh interface ipv4 set dnsserver name="{interface_name}" static {self.dns_servers[0]} primary'
            print(f"set_dns: Running command: {cmd_set_primary}")
            subprocess.run(cmd_set_primary, check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            cmd_set_secondary = f'netsh interface ipv4 add dnsserver name="{interface_name}" {self.dns_servers[1]} index=2'
            print(f"set_dns: Running command: {cmd_set_secondary}")
            subprocess.run(cmd_set_secondary, check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            self.update_ui_for_state(status_key="status_dns_on")
            print(f"DNS set to {self.dns_servers} for interface '{interface_name}'")
        except subprocess.CalledProcessError as e:
            print(f"set_dns: Failed to set DNS - {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
            self.update_ui_for_state(error_key="error_set_dns_failed")
        except FileNotFoundError as e:
            print(f"set_dns: FileNotFoundError - {e} (likely netsh)")
            self.update_ui_for_state(custom_message=persian_texts["error_netsh_not_found"])
        except Exception as e:
            print(f"set_dns: Generic error - {e}")
            self.update_ui_for_state(custom_message=str(e))
        print("set_dns: End")

    def clear_dns(self, interface_name):
        print(f"clear_dns: Start for interface '{interface_name}'")
        try:
            cmd_clear = f'netsh interface ipv4 set dnsserver name="{interface_name}" source=dhcp'
            print(f"clear_dns: Running command: {cmd_clear}")
            subprocess.run(cmd_clear, check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

            self.update_ui_for_state(status_key="status_dns_off")
            print(f"DNS cleared for interface '{interface_name}'")
        except subprocess.CalledProcessError as e:
            print(f"clear_dns: Failed to clear DNS - {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
            self.update_ui_for_state(error_key="error_clear_dns_failed")
        except FileNotFoundError as e:
            print(f"clear_dns: FileNotFoundError - {e} (likely netsh)")
            self.update_ui_for_state(custom_message=persian_texts["error_netsh_not_found"])
        except Exception as e:
            print(f"clear_dns: Generic error - {e}")
            self.update_ui_for_state(custom_message=str(e))
        print("clear_dns: End")

    def get_current_dns_servers(self, interface_name):
        print(f"get_current_dns_servers: Start for interface '{interface_name}'")
        current_dns_list = []
        try:
            cmd = f'netsh interface ipv4 show dnsservers name="{interface_name}"'
            print(f"get_current_dns_servers: Running command: {cmd}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                line_strip = line.strip()
                if line_strip and "---" not in line_strip and "Configuration for interface" not in line_strip and "Statically Configured DNS Servers" not in line_strip and "Register with which suffix" not in line_strip:
                    import re
                    ip_found = re.findall(r'\b(?:[0-9]{1,3}\\.){3}[0-9]{1,3}\b', line_strip)
                    if ip_found: current_dns_list.extend(ip_found)
            return current_dns_list
        except subprocess.CalledProcessError as e:
            print(f"get_current_dns_servers: subprocess.CalledProcessError - {e}\nOutput: {e.stdout}\nError: {e.stderr}")
            # No UI update here, as this is usually part of a larger check
        except FileNotFoundError as e:
            print(f"get_current_dns_servers: FileNotFoundError - {e} (likely netsh)")
            self.update_ui_for_state(custom_message=persian_texts["error_netsh_not_found"])
        except Exception as e:
            print(f"get_current_dns_servers: Generic error - {e}")
            self.update_ui_for_state(custom_message=str(e))
        print("get_current_dns_servers: End, returning []")
        return []

    def check_initial_dns_state(self):
        print("check_initial_dns_state: Start")
        interface_name = self.get_active_interface_name()
        if interface_name:
            print(f"check_initial_dns_state: Active interface found: '{interface_name}'")
            current_dns = self.get_current_dns_servers(interface_name)
            print(f"check_initial_dns_state: Current DNS servers: {current_dns}")
            if len(current_dns) >= 2 and current_dns[0] == self.dns_servers[0] and current_dns[1] == self.dns_servers[1]:
                print("check_initial_dns_state: Custom DNS is ON")
                self.update_ui_for_state(status_key="status_dns_on")
            else:
                print("check_initial_dns_state: Custom DNS is OFF")
                self.update_ui_for_state(status_key="status_dns_off")
        else:
            print("check_initial_dns_state: No active network interface found. Disabling button.")
            self.update_ui_for_state(interface_error=True) # Specific message for startup
            self.toggle_switch.config(state=tk.DISABLED)
        print("check_initial_dns_state: End")

    def toggle_dns(self):
        print("toggle_dns: Start")
        if not self.is_admin():
            print("toggle_dns: Not admin!")
            # Status already set by __init__ if not admin initially
            # self.update_ui_for_state(admin_error=True)
            return

        interface_name = self.get_active_interface_name()
        if not interface_name:
            print("toggle_dns: No active interface found for toggle.")
            self.update_ui_for_state(error_key="error_toggle_no_active_interface")
            return
        
        print(f"Toggling DNS for interface: '{interface_name}'")
        if self.dns_on:
            print("toggle_dns: DNS is ON, attempting to clear...")
            self.clear_dns(interface_name)
        else:
            print("toggle_dns: DNS is OFF, attempting to set...")
            self.set_dns(interface_name)
        print("toggle_dns: End")

def main():
    print("Starting main function...")
    root = tk.Tk()
    # root.configure(bg="#ECECEC") # Covered by gradient canvas
    try:
        print("Initializing DNSToggler app...")
        app = DNSToggler(root)
        print("DNSToggler app initialized. Starting mainloop...")
        root.mainloop()
        print("Exited mainloop.")
    except Exception as e:
        print(f"MAIN EXCEPTION: An error occurred: {e}")
        error_type = type(e).__name__
        print(f"MAIN EXCEPTION Type: {error_type}")
        import traceback
        print("MAIN EXCEPTION Traceback:")
        traceback.print_exc()
        try:
            from tkinter import messagebox # Ensure messagebox is imported here too
            messagebox.showerror(
                persian_texts["app_error_title"],
                f"{persian_texts['app_error_unexpected']}\n{error_type}: {e}"
            )
        except ImportError:
            pass 
        except tk.TclError:
            print(persian_texts["main_exception_tclerror_messagebox"])

if __name__ == "__main__":
    print(f"Script __name__ is {__name__}. Running main()...")
    main() 
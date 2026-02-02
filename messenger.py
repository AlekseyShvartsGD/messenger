import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import os
import platform
import sys
import threading
import time
import json
import socket
import select
import hashlib
import getpass
import subprocess
import base64
import struct
from pathlib import Path

class LocalMessenger:
    def __init__(self):
        self.root = tk.Tk()
        
        # Window setup
        self.root.title("Operation")
        self.root.geometry("550x650")  # Increased size for file transfer
        self.root.configure(bg='#1a1a1a')
        
        # User and connection state
        self.current_user = None
        self.user_id = None
        self.user_ip = None
        self.user_port = 12345
        self.file_port = 12346  # Separate port for file transfers
        
        # Messenger state
        self.messenger_active = False
        self.messenger_server = None
        self.file_server = None
        self.connected_users = {}  # user_id: socket
        self.user_directory = {}   # user_id: {"name": "", "ip": "", "last_seen": ""}
        
        # File transfer state
        self.file_transfers = {}  # transfer_id: {type, filename, size, progress, status}
        self.current_file_transfer_id = 0
        
        # Platform-specific paths
        self.system = platform.system()
        
        # Configuration files
        if self.system == "Windows":
            self.app_data_dir = os.path.join(os.getenv('APPDATA'), 'LocalMessenger')
            self.download_dir = os.path.join(os.getenv('USERPROFILE'), 'Downloads', 'Operation')
        else:  # Linux, macOS, etc.
            self.app_data_dir = os.path.expanduser("~/.localmessenger")
            self.download_dir = os.path.expanduser("~/Downloads/Operation")
        
        self.config_file = os.path.join(self.app_data_dir, 'config.json')
        self.contacts_file = os.path.join(self.app_data_dir, 'contacts.json')
        
        # Create app data directory
        os.makedirs(self.app_data_dir, exist_ok=True)
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Load configuration
        self.load_config()
        
        # Setup auto-start
        self.setup_autostart()
        
        # If user already exists, start messenger directly
        if self.current_user and self.user_id:
            self.start_messenger()
        else:
            self.show_login_screen()
    
    def setup_autostart(self):
        """Setup auto-start based on platform"""
        if self.system == "Windows":
            self.setup_windows_autostart()
        elif self.system == "Linux":
            self.setup_linux_autostart()
        elif self.system == "Darwin":  # macOS
            self.setup_macos_autostart()
    
    def setup_windows_autostart(self):
        """Add app to Windows startup via Task Scheduler if not exists"""
        try:
            import winreg
            
            # First, try to check if task already exists in Task Scheduler
            task_name = "LocalMessengerNotification"
            check_command = f'schtasks /query /tn "{task_name}"'
            result = subprocess.run(check_command, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:  # Task doesn't exist
                # Get the path to the current executable/script
                if getattr(sys, 'frozen', False):
                    # Running as executable
                    app_path = sys.executable
                else:
                    # Running as script
                    app_path = sys.argv[0]
                    # If it's a script, we need to run it with Python
                    python_exe = sys.executable
                    app_path = f'"{python_exe}" "{app_path}"'
                
                # Create the task using schtasks command
                create_command = f'''
schtasks /create /tn "{task_name}" /tr "{app_path}" /sc onlogon /rl highest /f
'''
                subprocess.run(create_command, shell=True, capture_output=True)
                
                # Also add to registry as backup
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0, winreg.KEY_SET_VALUE
                    )
                    winreg.SetValueEx(key, "LocalMessenger", 0, winreg.REG_SZ, app_path)
                    winreg.CloseKey(key)
                except:
                    pass
                
                print("Windows autostart task created successfully")
            else:
                print("Windows autostart task already exists")
                
        except Exception as e:
            print(f"Windows autostart setup failed: {e}")
    
    def setup_linux_autostart(self):
        """Add app to Linux startup (systemd user service)"""
        try:
            # Create systemd user service directory
            service_dir = os.path.expanduser(f"~/.config/systemd/user")
            os.makedirs(service_dir, exist_ok=True)
            
            # Get the path to the Python script
            if getattr(sys, 'frozen', False):
                # Running as executable
                script_path = sys.executable
                exec_start = f'"{script_path}"'
            else:
                # Running as script
                script_path = os.path.abspath(sys.argv[0])
                exec_start = f'/usr/bin/env python3 "{script_path}"'
            
            # Check if service already exists
            service_file = os.path.join(service_dir, "local-messenger.service")
            
            if not os.path.exists(service_file):
                # Create the service file content
                service_content = f"""[Unit]
Description=Local Messenger
After=network.target graphical-session.target

[Service]
Type=simple
ExecStart={exec_start}
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
"""
                
                # Write the service file
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                # Enable the service
                subprocess.run([
                    "systemctl", "--user", "daemon-reload"
                ], capture_output=True)
                
                subprocess.run([
                    "systemctl", "--user", "enable", "local-messenger.service"
                ], capture_output=True)
                
                subprocess.run([
                    "systemctl", "--user", "start", "local-messenger.service"
                ], capture_output=True)
                
                print("Linux systemd service created and started")
            else:
                # Service exists, make sure it's running
                subprocess.run([
                    "systemctl", "--user", "start", "local-messenger.service"
                ], capture_output=True)
                print("Linux systemd service already exists, ensuring it's running")
            
            # Also add to desktop autostart (for older DEs)
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=Local Messenger
Exec={exec_start}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            
            desktop_file = os.path.join(autostart_dir, "local-messenger.desktop")
            if not os.path.exists(desktop_file):
                with open(desktop_file, 'w') as f:
                    f.write(desktop_content)
                
                # Make it executable
                os.chmod(desktop_file, 0o755)
                print("Linux desktop autostart entry created")
            
        except Exception as e:
            print(f"Linux autostart setup failed: {e}")
    
    def setup_macos_autostart(self):
        """Add app to macOS startup (launchd)"""
        try:
            # Get the path to the script/executable
            if getattr(sys, 'frozen', False):
                app_path = sys.executable
            else:
                app_path = os.path.abspath(sys.argv[0])
            
            # Create launch agent directory
            launch_agent_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(launch_agent_dir, exist_ok=True)
            
            # Launch agent plist file path
            plist_file = os.path.join(launch_agent_dir, "com.local.messenger.plist")
            
            if not os.path.exists(plist_file):
                # Create plist content
                if getattr(sys, 'frozen', False):
                    program_args = [app_path]
                else:
                    program_args = ["/usr/bin/python3", app_path]
                
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.messenger</string>
    <key>ProgramArguments</key>
    <array>
        <string>{program_args[0]}</string>
"""
                if len(program_args) > 1:
                    plist_content += f'        <string>{program_args[1]}</string>\n'
                
                plist_content += """    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/localmessenger.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/localmessenger.err</string>
</dict>
</plist>"""
                
                # Write plist file
                with open(plist_file, 'w') as f:
                    f.write(plist_content)
                
                # Load the launch agent
                subprocess.run([
                    "launchctl", "load", plist_file
                ], capture_output=True)
                
                print("macOS launch agent created and loaded")
            else:
                # Ensure it's loaded
                subprocess.run([
                    "launchctl", "load", plist_file
                ], capture_output=True)
                print("macOS launch agent already exists, ensuring it's loaded")
            
        except Exception as e:
            print(f"macOS autostart setup failed: {e}")
    
    def generate_user_id(self, username):
        """Generate unique user ID based on username and machine"""
        machine_id = platform.node()  # Computer name
        timestamp = str(time.time())
        combined = f"{username}_{machine_id}_{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()[:8]  # 8-char user ID
    
    def get_local_ip(self):
        """Get local IP address - cross-platform"""
        try:
            if self.system == "Windows":
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            else:  # Linux/macOS
                # Try multiple methods for Linux
                try:
                    import netifaces
                    for interface in netifaces.interfaces():
                        addrs = netifaces.ifaddresses(interface)
                        if netifaces.AF_INET in addrs:
                            for addr_info in addrs[netifaces.AF_INET]:
                                ip = addr_info['addr']
                                if ip != '127.0.0.1' and not ip.startswith('169.254'):
                                    return ip
                except ImportError:
                    # Fallback method
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def load_config(self):
        """Load saved configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_user = config.get('username')
                    self.user_id = config.get('user_id')
                    self.user_ip = config.get('user_ip')
                    self.user_port = config.get('port', 12345)
            
            if os.path.exists(self.contacts_file):
                with open(self.contacts_file, 'r') as f:
                    self.user_directory = json.load(f)
        except:
            pass
    
    def save_config(self):
        """Save configuration"""
        config = {
            'username': self.current_user,
            'user_id': self.user_id,
            'user_ip': self.user_ip,
            'port': self.user_port
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Save contacts
        with open(self.contacts_file, 'w') as f:
            json.dump(self.user_directory, f, indent=2)
    
    def show_login_screen(self):
        """Show login/register screen"""
        self.clear_window()
        
        # Title
        title_label = tk.Label(
            self.root,
            text="Operation",
            font=('Arial', 16, 'bold'),
            fg='#00BCD4',
            bg='#1a1a1a'
        )
        title_label.pack(pady=(30, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            self.root,
            text="Connect with users on your local network",
            font=('Arial', 10),
            fg='#AAAAAA',
            bg='#1a1a1a'
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Username entry
        username_frame = tk.Frame(self.root, bg='#1a1a1a')
        username_frame.pack(pady=10)
        
        tk.Label(
            username_frame,
            text="Choose a username:",
            font=('Arial', 11),
            fg='white',
            bg='#1a1a1a'
        ).pack(side='left', padx=(0, 10))
        
        self.username_entry = tk.Entry(
            username_frame,
            font=('Arial', 11),
            width=20,
            bg='#2a2a2a',
            fg='white',
            insertbackground='white'
        )
        self.username_entry.pack(side='left')
        
        # OS username as suggestion
        try:
            os_user = getpass.getuser()
            self.username_entry.insert(0, os_user)
        except:
            pass
        
        # Login button
        login_btn = tk.Button(
            self.root,
            text="Start Messaging",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#2196F3',
            command=self.login,
            width=20,
            height=2
        )
        login_btn.pack(pady=30)
        
        # Info
        info_label = tk.Label(
            self.root,
            text=f"• Auto-starts on {self.system} login\n• Share your User ID to connect\n• Works on local network only\n• Send files to contacts",
            font=('Arial', 9),
            fg='#666666',
            bg='#1a1a1a',
            justify='left'
        )
        info_label.pack(pady=20)
    
    def login(self):
        """Login/register user"""
        username = self.username_entry.get().strip()
        if not username:
            return
        
        self.current_user = username
        self.user_id = self.generate_user_id(username)
        self.user_ip = self.get_local_ip()
        
        # Add self to directory
        self.user_directory[self.user_id] = {
            "name": self.current_user,
            "ip": self.user_ip,
            "last_seen": datetime.now().isoformat(),
            "is_online": True
        }
        
        # Save config
        self.save_config()
        
        # Start messenger
        self.start_messenger()
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def start_messenger(self):
        """Start the messenger interface"""
        self.clear_window()
        
        # Start messenger server
        self.start_messenger_server()
        
        # Start file server
        self.start_file_server()
        
        # Create main interface
        self.create_messenger_interface()
        
        # Start background thread for checking messages
        self.messenger_active = True
        threading.Thread(target=self.check_messages, daemon=True).start()
        threading.Thread(target=self.check_file_transfers, daemon=True).start()
        
        # Broadcast presence
        self.broadcast_presence()
    
    def start_messenger_server(self):
        """Start server to listen for connections"""
        try:
            self.messenger_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.messenger_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.messenger_server.bind(('0.0.0.0', self.user_port))
            self.messenger_server.listen(5)
            self.messenger_server.setblocking(False)
        except Exception as e:
            print(f"Error starting messenger server: {e}")
    
    def start_file_server(self):
        """Start file transfer server"""
        try:
            self.file_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.file_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.file_server.bind(('0.0.0.0', self.file_port))
            self.file_server.listen(5)
            self.file_server.setblocking(False)
        except Exception as e:
            print(f"Error starting file server: {e}")
    
    def create_messenger_interface(self):
        """Create the main messenger interface"""
        # Top bar
        top_bar = tk.Frame(self.root, bg='#2a2a2a', height=50)
        top_bar.pack(fill='x', pady=(0, 5))
        
        # User info
        user_info_frame = tk.Frame(top_bar, bg='#2a2a2a')
        user_info_frame.pack(side='left', padx=10)
        
        tk.Label(
            user_info_frame,
            text=f"👤 {self.current_user}",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#2a2a2a'
        ).pack(side='left')
        
        # User ID display with copy button
        id_frame = tk.Frame(top_bar, bg='#2a2a2a')
        id_frame.pack(side='right', padx=10)
        
        tk.Label(
            id_frame,
            text="Your ID:",
            font=('Arial', 9),
            fg='#AAAAAA',
            bg='#2a2a2a'
        ).pack(side='left')
        
        id_display = tk.Label(
            id_frame,
            text=self.user_id,
            font=('Arial', 9, 'bold'),
            fg='#00FF00',
            bg='#2a2a2a'
        )
        id_display.pack(side='left', padx=5)
        
        copy_btn = tk.Button(
            id_frame,
            text="📋",
            font=('Arial', 9),
            fg='white',
            bg='#555555',
            command=lambda: self.copy_to_clipboard(self.user_id),
            width=3
        )
        copy_btn.pack(side='left', padx=(5, 0))
        
        # Platform indicator
        platform_frame = tk.Frame(top_bar, bg='#2a2a2a')
        platform_frame.pack(side='left', padx=10)
        
        platform_icon = "🐧" if self.system == "Linux" else "🪟" if self.system == "Windows" else "💻"
        tk.Label(
            platform_frame,
            text=platform_icon,
            font=('Arial', 12),
            fg='white',
            bg='#2a2a2a'
        ).pack(side='left', padx=5)
        
        # SEARCH BAR
        search_frame = tk.Frame(self.root, bg='#1a1a1a')
        search_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            search_frame,
            text="🔍 Search:",
            font=('Arial', 9),
            fg='#AAAAAA',
            bg='#1a1a1a'
        ).pack(side='left')
        
        self.search_entry = tk.Entry(
            search_frame,
            font=('Arial', 9),
            width=25,
            bg='#2a2a2a',
            fg='white',
            insertbackground='white'
        )
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', self.perform_search)
        
        clear_search_btn = tk.Button(
            search_frame,
            text="Clear",
            font=('Arial', 9),
            fg='white',
            bg='#555555',
            command=self.clear_search,
            width=6
        )
        clear_search_btn.pack(side='left', padx=5)
        
        # File transfer button
        file_btn = tk.Button(
            search_frame,
            text="📁 Send File",
            font=('Arial', 9),
            fg='white',
            bg='#4CAF50',
            command=self.send_file_dialog,
            width=10
        )
        file_btn.pack(side='left', padx=(10, 0))
        
        # Contacts/Connect frame
        connect_frame = tk.Frame(self.root, bg='#1a1a1a')
        connect_frame.pack(fill='x', padx=10, pady=5)
        
        # Add contact section
        add_frame = tk.Frame(connect_frame, bg='#1a1a1a')
        add_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(
            add_frame,
            text="Connect to User ID:",
            font=('Arial', 9),
            fg='#AAAAAA',
            bg='#1a1a1a'
        ).pack(side='left')
        
        self.connect_id_entry = tk.Entry(
            add_frame,
            font=('Arial', 9),
            width=12,
            bg='#2a2a2a',
            fg='white',
            insertbackground='white'
        )
        self.connect_id_entry.pack(side='left', padx=5)
        
        self.connect_btn = tk.Button(
            add_frame,
            text="Connect",
            font=('Arial', 9),
            fg='white',
            bg='#2196F3',
            command=self.connect_to_user,
            width=8
        )
        self.connect_btn.pack(side='left', padx=5)
        
        refresh_btn = tk.Button(
            add_frame,
            text="🔄 Refresh",
            font=('Arial', 9),
            fg='white',
            bg='#555555',
            command=self.refresh_contacts,
            width=10
        )
        refresh_btn.pack(side='left', padx=5)
        
        # Contacts list
        contacts_frame = tk.Frame(self.root, bg='#1a1a1a')
        contacts_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Contacts header with count
        contacts_header = tk.Frame(contacts_frame, bg='#1a1a1a')
        contacts_header.pack(fill='x', pady=(0, 5))
        
        tk.Label(
            contacts_header,
            text="Contacts:",
            font=('Arial', 10, 'bold'),
            fg='white',
            bg='#1a1a1a'
        ).pack(side='left')
        
        self.contacts_count_label = tk.Label(
            contacts_header,
            text="",
            font=('Arial', 9),
            fg='#666666',
            bg='#1a1a1a'
        )
        self.contacts_count_label.pack(side='left', padx=10)
        
        # Contacts listbox with scrollbar
        listbox_frame = tk.Frame(contacts_frame, bg='#1a1a1a')
        listbox_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.contacts_listbox = tk.Listbox(
            listbox_frame,
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='white',
            selectbackground='#3a3a3a',
            yscrollcommand=scrollbar.set,
            height=6
        )
        self.contacts_listbox.pack(side='left', fill='both', expand=True)
        self.contacts_listbox.bind('<<ListboxSelect>>', self.on_contact_select)
        
        scrollbar.config(command=self.contacts_listbox.yview)
        
        # File transfers frame
        transfers_frame = tk.Frame(self.root, bg='#1a1a1a')
        transfers_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            transfers_frame,
            text="📁 Active Transfers:",
            font=('Arial', 9, 'bold'),
            fg='white',
            bg='#1a1a1a'
        ).pack(side='left')
        
        self.transfers_label = tk.Label(
            transfers_frame,
            text="0 active",
            font=('Arial', 9),
            fg='#FF8800',
            bg='#1a1a1a'
        )
        self.transfers_label.pack(side='left', padx=10)
        
        # Chat area
        chat_frame = tk.Frame(self.root, bg='#1a1a1a')
        chat_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Chat display
        chat_display_frame = tk.Frame(chat_frame, bg='#1a1a1a')
        chat_display_frame.pack(fill='both', expand=True)
        
        scrollbar_chat = tk.Scrollbar(chat_display_frame)
        scrollbar_chat.pack(side='right', fill='y')
        
        self.chat_display = tk.Text(
            chat_display_frame,
            font=('Arial', 10),
            bg='#0a0a0a',
            fg='white',
            wrap='word',
            yscrollcommand=scrollbar_chat.set,
            state='disabled',
            height=6
        )
        self.chat_display.pack(fill='both', expand=True)
        
        scrollbar_chat.config(command=self.chat_display.yview)
        
        # Message input
        input_frame = tk.Frame(chat_frame, bg='#1a1a1a')
        input_frame.pack(fill='x', pady=(5, 0))
        
        self.message_entry = tk.Entry(
            input_frame,
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='white',
            insertbackground='white'
        )
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', self.send_chat_message)
        
        # Attach file button
        attach_btn = tk.Button(
            input_frame,
            text="📎",
            font=('Arial', 12),
            fg='white',
            bg='#FF9800',
            command=self.send_file_to_selected,
            width=3
        )
        attach_btn.pack(side='left', padx=(0, 5))
        
        self.send_btn = tk.Button(
            input_frame,
            text="Send",
            font=('Arial', 10, 'bold'),
            fg='white',
            bg='#0088cc',
            command=self.send_chat_message,
            width=8
        )
        self.send_btn.pack(side='right')
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text=f"Ready to chat. Share your User ID: {self.user_id} | Platform: {self.system}",
            font=('Arial', 8),
            fg='#FF8800',
            bg='#1a1a1a'
        )
        self.status_label.pack(pady=(0, 5))
        
        # Selected contact
        self.selected_contact_id = None
        
        # Update contacts list
        self.update_contacts_list()
        
        # Add welcome message
        self.add_chat_message("Welcome to Local Messenger!", "system")
        self.add_chat_message(f"Your User ID: {self.user_id}", "system")
        self.add_chat_message(f"Platform: {self.system}", "system")
        self.add_chat_message("Share your ID with others to connect", "system")
        self.add_chat_message("Click 📎 to send files to selected contact", "system")
        self.add_chat_message(f"Files are saved to: {self.download_dir}", "system")
    
    def send_file_dialog(self):
        """Open file dialog to send file"""
        if not self.selected_contact_id:
            messagebox.showwarning("No Contact Selected", "Please select a contact first.")
            return
        
        filename = filedialog.askopenfilename(
            title="Select file to send",
            filetypes=[
                ("All files", "*.*"),
                ("Text files", "*.txt"),
                ("Images", "*.png *.jpg *.jpeg *.gif"),
                ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx"),
                ("Videos", "*.mp4 *.avi *.mkv *.mov"),
                ("Audio", "*.mp3 *.wav *.flac")
            ]
        )
        
        if filename:
            self.send_file(self.selected_contact_id, filename)
    
    def send_file_to_selected(self):
        """Send file to selected contact"""
        if not self.selected_contact_id:
            self.status_label.config(text="✗ Select a contact first", fg='#FF0000')
            return
        self.send_file_dialog()
    
    def send_file(self, user_id, filepath):
        """Send a file to a user"""
        try:
            if not os.path.exists(filepath):
                self.add_chat_message(f"File not found: {filepath}", "system")
                return
            
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            
            if filesize > 100 * 1024 * 1024:  # 100MB limit
                self.add_chat_message(f"File too large: {filename} ({filesize/1024/1024:.1f}MB)", "system")
                return
            
            # Generate transfer ID
            transfer_id = self.current_file_transfer_id
            self.current_file_transfer_id += 1
            
            # Add to transfers
            self.file_transfers[transfer_id] = {
                'type': 'sending',
                'filename': filename,
                'size': filesize,
                'progress': 0,
                'status': 'pending',
                'user_id': user_id,
                'filepath': filepath
            }
            
            # Update transfers display
            self.update_transfers_display()
            
            # Send file request
            if user_id in self.connected_users:
                file_request = json.dumps({
                    'type': 'file_request',
                    'from_id': self.user_id,
                    'from_name': self.current_user,
                    'filename': filename,
                    'filesize': filesize,
                    'transfer_id': transfer_id
                })
                self.connected_users[user_id].send(file_request.encode('utf-8'))
                
                self.add_chat_message(f"📁 Sending file: {filename} ({filesize/1024/1024:.1f}MB)", "system")
                self.status_label.config(text=f"📁 Sending file: {filename}", fg='#00FF00')
                
                # Start file transfer thread
                threading.Thread(target=self.send_file_thread, 
                               args=(user_id, filepath, transfer_id), daemon=True).start()
            else:
                self.add_chat_message(f"User not connected", "system")
                del self.file_transfers[transfer_id]
                
        except Exception as e:
            self.add_chat_message(f"Error sending file: {str(e)}", "system")
    
    def send_file_thread(self, user_id, filepath, transfer_id):
        """Thread for sending file"""
        try:
            # Connect to user's file port
            if user_id not in self.user_directory:
                self.root.after(0, lambda: self.add_chat_message("User not found", "system"))
                return
            
            user_ip = self.user_directory[user_id]['ip']
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(30)
            client_socket.connect((user_ip, self.file_port))
            
            # Send file metadata
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            
            metadata = json.dumps({
                'type': 'file_metadata',
                'filename': filename,
                'filesize': filesize,
                'transfer_id': transfer_id,
                'sender_id': self.user_id,
                'sender_name': self.current_user
            })
            
            # Send metadata length first
            metadata_len = len(metadata)
            client_socket.send(struct.pack('!I', metadata_len))
            client_socket.send(metadata.encode('utf-8'))
            
            # Wait for acknowledgment
            ack = client_socket.recv(1024).decode('utf-8')
            if ack != 'READY':
                raise Exception("Receiver not ready")
            
            # Send file data
            sent_bytes = 0
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    client_socket.send(chunk)
                    sent_bytes += len(chunk)
                    
                    # Update progress
                    progress = (sent_bytes / filesize) * 100
                    if transfer_id in self.file_transfers:
                        self.file_transfers[transfer_id]['progress'] = progress
                        self.root.after(0, self.update_transfers_display)
            
            # Wait for completion acknowledgment
            completion = client_socket.recv(1024).decode('utf-8')
            if completion == 'COMPLETE':
                if transfer_id in self.file_transfers:
                    self.file_transfers[transfer_id]['status'] = 'completed'
                    self.file_transfers[transfer_id]['progress'] = 100
                    self.root.after(0, self.update_transfers_display)
                    self.root.after(0, lambda: self.add_chat_message(f"✓ File sent: {filename}", "system"))
            else:
                raise Exception("Transfer failed")
            
            client_socket.close()
            
        except Exception as e:
            if transfer_id in self.file_transfers:
                self.file_transfers[transfer_id]['status'] = 'failed'
                self.root.after(0, self.update_transfers_display)
                self.root.after(0, lambda: self.add_chat_message(f"✗ File transfer failed: {str(e)}", "system"))
    
    def check_file_transfers(self):
        """Check for incoming file transfers"""
        while self.messenger_active and self.file_server:
            try:
                readable, _, _ = select.select([self.file_server], [], [], 0.1)
                
                for sock in readable:
                    if sock == self.file_server:
                        # New file transfer connection
                        client_socket, addr = self.file_server.accept()
                        threading.Thread(target=self.handle_file_transfer, 
                                       args=(client_socket, addr), daemon=True).start()
                
            except Exception as e:
                time.sleep(0.1)
    
    def handle_file_transfer(self, sock, addr):
        """Handle incoming file transfer"""
        try:
            sock.settimeout(30)
            
            # Receive metadata length
            metadata_len_data = sock.recv(4)
            if not metadata_len_data:
                sock.close()
                return
            
            metadata_len = struct.unpack('!I', metadata_len_data)[0]
            
            # Receive metadata
            metadata = sock.recv(metadata_len).decode('utf-8')
            metadata_json = json.loads(metadata)
            
            filename = metadata_json.get('filename')
            filesize = metadata_json.get('filesize')
            transfer_id = metadata_json.get('transfer_id')
            sender_id = metadata_json.get('sender_id')
            sender_name = metadata_json.get('sender_name', 'Unknown')
            
            # Send ready signal
            sock.send('READY'.encode('utf-8'))
            
            # Create unique filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{safe_filename}"
            save_path = os.path.join(self.download_dir, unique_filename)
            
            # Create transfer entry
            if transfer_id not in self.file_transfers:
                self.file_transfers[transfer_id] = {
                    'type': 'receiving',
                    'filename': filename,
                    'size': filesize,
                    'progress': 0,
                    'status': 'downloading',
                    'user_id': sender_id,
                    'save_path': save_path
                }
                self.root.after(0, self.update_transfers_display)
            
            # Receive file data
            received_bytes = 0
            with open(save_path, 'wb') as f:
                while received_bytes < filesize:
                    chunk = sock.recv(min(4096, filesize - received_bytes))
                    if not chunk:
                        break
                    f.write(chunk)
                    received_bytes += len(chunk)
                    
                    # Update progress
                    progress = (received_bytes / filesize) * 100
                    if transfer_id in self.file_transfers:
                        self.file_transfers[transfer_id]['progress'] = progress
                        self.root.after(0, self.update_transfers_display)
            
            # Send completion acknowledgment
            sock.send('COMPLETE'.encode('utf-8'))
            sock.close()
            
            # Update transfer status
            if transfer_id in self.file_transfers:
                self.file_transfers[transfer_id]['status'] = 'completed'
                self.file_transfers[transfer_id]['progress'] = 100
                self.root.after(0, self.update_transfers_display)
                
                # Show notification
                self.root.after(0, lambda: self.add_chat_message(
                    f"📁 Received file from {sender_name}: {filename}", "system"))
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✓ File received: {filename}", fg='#00FF00'))
                
                # Open file location button
                self.root.after(3000, lambda: self.show_file_received_notification(save_path, filename))
            
        except Exception as e:
            print(f"File transfer error: {e}")
            if transfer_id in self.file_transfers:
                self.file_transfers[transfer_id]['status'] = 'failed'
                self.root.after(0, self.update_transfers_display)
            try:
                sock.close()
            except:
                pass
    
    def show_file_received_notification(self, filepath, filename):
        """Show notification for received file"""
        if hasattr(self, 'status_label'):
            # Create a frame for the notification
            notification_frame = tk.Frame(self.root, bg='#2a2a2a', relief='raised', bd=1)
            notification_frame.place(relx=0.5, rely=0.9, anchor='center')
            
            label = tk.Label(
                notification_frame,
                text=f"📁 {filename} received",
                font=('Arial', 9),
                fg='white',
                bg='#2a2a2a'
            )
            label.pack(side='left', padx=10, pady=5)
            
            open_btn = tk.Button(
                notification_frame,
                text="Open Folder",
                font=('Arial', 9),
                fg='white',
                bg='#2196F3',
                command=lambda: self.open_file_location(filepath),
                width=10
            )
            open_btn.pack(side='left', padx=(0, 10), pady=5)
            
            # Auto-hide after 10 seconds
            self.root.after(10000, notification_frame.destroy)
    
    def open_file_location(self, filepath):
        """Open file location in file explorer"""
        try:
            if self.system == "Windows":
                os.startfile(os.path.dirname(filepath))
            elif self.system == "Darwin":  # macOS
                subprocess.run(['open', os.path.dirname(filepath)])
            else:  # Linux
                subprocess.run(['xdg-open', os.path.dirname(filepath)])
        except Exception as e:
            print(f"Error opening file location: {e}")
    
    def update_transfers_display(self):
        """Update file transfers display"""
        active_count = sum(1 for t in self.file_transfers.values() 
                          if t['status'] in ['downloading', 'uploading', 'pending'])
        self.transfers_label.config(text=f"{active_count} active")
    
    def perform_search(self, event=None):
        """Search contacts by username or user ID"""
        search_term = self.search_entry.get().strip().lower()
        
        if not search_term:
            self.update_contacts_list()
            return
        
        self.contacts_listbox.delete(0, tk.END)
        found_count = 0
        
        for user_id, info in self.user_directory.items():
            if user_id == self.user_id:
                continue
            
            name = info.get("name", "Unknown").lower()
            is_online = user_id in self.connected_users
            
            if search_term in name or search_term in user_id.lower():
                status = "🟢" if is_online else "⚫"
                display_text = f"{status} {info['name']} ({user_id})"
                
                self.contacts_listbox.insert(tk.END, display_text)
                if is_online:
                    self.contacts_listbox.itemconfig(tk.END, foreground='#00FF00')
                else:
                    self.contacts_listbox.itemconfig(tk.END, foreground='#666666')
                
                found_count += 1
        
        self.contacts_count_label.config(text=f"Found: {found_count}")
        
        if found_count == 0 and search_term:
            self.contacts_listbox.insert(tk.END, "No users found. Try a different search.")
            self.contacts_listbox.itemconfig(tk.END, foreground='#FF4444')
    
    def clear_search(self):
        """Clear search field and show all contacts"""
        self.search_entry.delete(0, tk.END)
        self.update_contacts_list()
    
    def update_contacts_list(self):
        """Update the contacts listbox"""
        self.contacts_listbox.delete(0, tk.END)
        
        online_count = 0
        offline_count = 0
        
        # First show online users
        for user_id, info in self.user_directory.items():
            if user_id == self.user_id:
                continue
            
            if user_id in self.connected_users:  # Online
                name = info.get("name", "Unknown")
                status = "🟢"
                display_text = f"{status} {name} ({user_id})"
                
                self.contacts_listbox.insert(tk.END, display_text)
                self.contacts_listbox.itemconfig(tk.END, foreground='#00FF00')
                online_count += 1
        
        # Then show offline users
        for user_id, info in self.user_directory.items():
            if user_id == self.user_id:
                continue
            
            if user_id not in self.connected_users:  # Offline
                name = info.get("name", "Unknown")
                status = "⚫"
                display_text = f"{status} {name} ({user_id})"
                
                self.contacts_listbox.insert(tk.END, display_text)
                self.contacts_listbox.itemconfig(tk.END, foreground='#666666')
                offline_count += 1
        
        self.contacts_count_label.config(text=f"Online: {online_count} | Offline: {offline_count}")
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_label.config(text="✓ Copied to clipboard!", fg='#00FF00')
        self.root.after(2000, lambda: self.status_label.config(
            text=f"Ready to chat. Share your User ID: {self.user_id} | Platform: {self.system}",
            fg='#FF8800'
        ))
    
    def connect_to_user(self):
        """Connect to a user by ID"""
        user_id = self.connect_id_entry.get().strip()
        if not user_id:
            self.status_label.config(text="✗ Enter a User ID", fg='#FF0000')
            return
        
        if user_id == self.user_id:
            self.status_label.config(text="✗ Cannot connect to yourself", fg='#FF0000')
            return
        
        if user_id in self.user_directory:
            user_info = self.user_directory[user_id]
            self.try_connect_to_user(user_id, user_info["ip"])
        else:
            self.status_label.config(text="✗ User ID not found", fg='#FF0000')
    
    def try_connect_to_user(self, user_id, ip):
        """Try to connect to user"""
        threading.Thread(target=self.connect_thread, args=(user_id, ip), daemon=True).start()
    
    def connect_thread(self, user_id, ip):
        """Thread for connecting to user"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((ip, self.user_port))
            client_socket.setblocking(False)
            
            connect_msg = json.dumps({
                'type': 'connect',
                'user_id': self.user_id,
                'name': self.current_user,
                'ip': self.user_ip,
                'file_port': self.file_port
            })
            client_socket.send(connect_msg.encode('utf-8'))
            
            self.connected_users[user_id] = client_socket
            
            if user_id not in self.user_directory:
                self.user_directory[user_id] = {
                    "name": "Unknown",
                    "ip": ip,
                    "last_seen": datetime.now().isoformat(),
                    "is_online": True,
                    "file_port": self.file_port
                }
            
            self.root.after(0, self.status_label.config,
                          {"text": f"✓ Connected to user", "fg": '#00FF00'})
            self.root.after(0, self.update_contacts_list)
            
        except Exception as e:
            self.root.after(0, self.status_label.config,
                          {"text": f"✗ Connection failed: {str(e)}", "fg": '#FF0000'})
    
    def on_contact_select(self, event):
        """Handle contact selection"""
        selection = self.contacts_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        item_text = self.contacts_listbox.get(index)
        
        if "(" in item_text and ")" in item_text:
            start = item_text.rfind("(") + 1
            end = item_text.rfind(")")
            user_id = item_text[start:end]
            
            if user_id in self.user_directory:
                self.selected_contact_id = user_id
                user_name = self.user_directory[user_id].get("name", "Unknown")
                
                self.chat_display.config(state='normal')
                self.chat_display.delete('1.0', tk.END)
                self.chat_display.config(state='disabled')
                
                self.add_chat_message(f"Chat with {user_name}", "system")
                self.add_chat_message(f"Click 📎 to send files", "system")
                
                self.message_entry.config(state='normal')
                self.send_btn.config(state='normal')
    
    def add_chat_message(self, message, sender="system"):
        """Add a message to chat display"""
        self.chat_display.config(state='normal')
        
        if not self.chat_display.tag_names():
            self.chat_display.tag_config("you", foreground="#0088cc", font=('Arial', 10, 'bold'))
            self.chat_display.tag_config("other", foreground="#00aa00", font=('Arial', 10, 'bold'))
            self.chat_display.tag_config("system", foreground="#ff8800", font=('Arial', 10, 'italic'))
            self.chat_display.tag_config("timestamp", foreground="#666666", font=('Arial', 9))
            self.chat_display.tag_config("file", foreground="#4CAF50", font=('Arial', 10, 'bold'))
        
        timestamp = datetime.now().strftime("%H:%M")
        
        if sender == self.current_user or sender == "you":
            tag = "you"
            display_sender = "You"
        elif sender == "system":
            tag = "system"
            display_sender = "System"
        elif sender == "file":
            tag = "file"
            display_sender = "File"
        else:
            tag = "other"
            display_sender = sender
        
        if sender == "system":
            self.chat_display.insert('end', f"[{timestamp}] {message}\n", tag)
        else:
            self.chat_display.insert('end', f"[{timestamp}] {display_sender}: {message}\n", tag)
        
        lines = self.chat_display.get('1.0', 'end').split('\n')
        if len(lines) > 100:
            self.chat_display.delete('1.0', f'{len(lines)-100}.0')
        
        self.chat_display.config(state='disabled')
        self.chat_display.see('end')
    
    def send_chat_message(self, event=None):
        """Send chat message to selected contact"""
        if not self.selected_contact_id:
            self.status_label.config(text="✗ Select a contact first", fg='#FF0000')
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        self.message_entry.delete(0, tk.END)
        self.add_chat_message(message, "you")
        
        if self.selected_contact_id in self.connected_users:
            self.send_message_to_user(self.selected_contact_id, message)
        else:
            self.add_chat_message("Contact is not connected", "system")
    
    def send_message_to_user(self, user_id, message):
        """Send message to specific user"""
        try:
            if user_id in self.connected_users:
                msg_data = json.dumps({
                    'type': 'message',
                    'from_id': self.user_id,
                    'from_name': self.current_user,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                })
                self.connected_users[user_id].send(msg_data.encode('utf-8'))
        except:
            if user_id in self.connected_users:
                del self.connected_users[user_id]
            self.update_contacts_list()
            self.add_chat_message("Connection lost", "system")
    
    def broadcast_presence(self):
        """Broadcast presence to network"""
        pass
    
    def refresh_contacts(self):
        """Refresh contacts list"""
        self.update_contacts_list()
        self.status_label.config(text="✓ Contacts refreshed", fg='#00FF00')
        self.root.after(2000, lambda: self.status_label.config(
            text=f"Ready to chat. Share your User ID: {self.user_id} | Platform: {self.system}",
            fg='#FF8800'
        ))
    
    def check_messages(self):
        """Check for incoming messages"""
        while self.messenger_active:
            try:
                sockets = [self.messenger_server] + list(self.connected_users.values())
                readable, _, _ = select.select(sockets, [], [], 0.1)
                
                for sock in readable:
                    if sock == self.messenger_server:
                        client_socket, addr = self.messenger_server.accept()
                        client_socket.setblocking(False)
                        threading.Thread(target=self.handle_new_connection, 
                                       args=(client_socket, addr), daemon=True).start()
                    else:
                        try:
                            data = sock.recv(4096)
                            if data:
                                self.process_incoming_data(data, sock)
                            else:
                                self.remove_connection(sock)
                        except:
                            self.remove_connection(sock)
                
            except Exception as e:
                time.sleep(0.1)
    
    def handle_new_connection(self, sock, addr):
        """Handle new incoming connection"""
        try:
            sock.settimeout(5)
            data = sock.recv(1024)
            sock.setblocking(False)
            
            if data:
                self.process_incoming_data(data, sock)
        except:
            sock.close()
    
    def process_incoming_data(self, data, sock):
        """Process incoming data"""
        try:
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type')
            
            if msg_type == 'connect':
                user_id = message.get('user_id')
                user_name = message.get('name')
                user_ip = message.get('ip')
                file_port = message.get('file_port', self.file_port)
                
                self.user_directory[user_id] = {
                    "name": user_name,
                    "ip": user_ip,
                    "last_seen": datetime.now().isoformat(),
                    "is_online": True,
                    "file_port": file_port
                }
                
                self.connected_users[user_id] = sock
                self.save_config()
                
                self.root.after(0, self.update_contacts_list)
                self.root.after(0, self.add_chat_message,
                              f"{user_name} connected", "system")
                
                response = json.dumps({
                    'type': 'connect_ack',
                    'user_id': self.user_id,
                    'name': self.current_user,
                    'ip': self.user_ip,
                    'file_port': self.file_port
                })
                sock.send(response.encode('utf-8'))
            
            elif msg_type == 'connect_ack':
                user_id = message.get('user_id')
                user_name = message.get('name')
                user_ip = message.get('ip')
                file_port = message.get('file_port', self.file_port)
                
                self.user_directory[user_id] = {
                    "name": user_name,
                    "ip": user_ip,
                    "last_seen": datetime.now().isoformat(),
                    "is_online": True,
                    "file_port": file_port
                }
                
                self.save_config()
                self.root.after(0, self.update_contacts_list)
                self.root.after(0, self.add_chat_message,
                              f"Connected to {user_name}", "system")
            
            elif msg_type == 'message':
                from_id = message.get('from_id')
                from_name = message.get('from_name')
                msg_text = message.get('message')
                
                if from_id in self.user_directory:
                    self.user_directory[from_id]['last_seen'] = datetime.now().isoformat()
                    self.user_directory[from_id]['is_online'] = True
                
                if from_id == self.selected_contact_id:
                    self.root.after(0, self.add_chat_message, msg_text, from_name)
                else:
                    self.root.after(0, self.add_chat_message,
                                  f"New message from {from_name}", "system")
            
            elif msg_type == 'file_request':
                from_id = message.get('from_id')
                from_name = message.get('from_name')
                filename = message.get('filename')
                filesize = message.get('filesize')
                transfer_id = message.get('transfer_id')
                
                # Ask user to accept file
                self.root.after(0, self.show_file_request_dialog,
                              from_id, from_name, filename, filesize, transfer_id)
                
        except json.JSONDecodeError:
            pass
    
    def show_file_request_dialog(self, from_id, from_name, filename, filesize, transfer_id):
        """Show dialog to accept/reject file transfer"""
        filesize_mb = filesize / 1024 / 1024
        
        # Create a dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("File Transfer Request")
        dialog.configure(bg='#1a1a1a')
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Message
        message = f"{from_name} wants to send you a file:\n\n"
        message += f"📁 {filename}\n"
        message += f"📏 Size: {filesize_mb:.1f} MB\n\n"
        message += "Do you want to accept this file?"
        
        label = tk.Label(
            dialog,
            text=message,
            font=('Arial', 11),
            fg='white',
            bg='#1a1a1a',
            justify='left'
        )
        label.pack(pady=20, padx=20)
        
        # Buttons frame
        button_frame = tk.Frame(dialog, bg='#1a1a1a')
        button_frame.pack(pady=10)
        
        def accept_file():
            # Create transfer entry
            self.file_transfers[transfer_id] = {
                'type': 'receiving',
                'filename': filename,
                'size': filesize,
                'progress': 0,
                'status': 'pending',
                'user_id': from_id
            }
            self.update_transfers_display()
            
            # Send acceptance
            if from_id in self.connected_users:
                response = json.dumps({
                    'type': 'file_accept',
                    'transfer_id': transfer_id
                })
                self.connected_users[from_id].send(response.encode('utf-8'))
            
            dialog.destroy()
            self.add_chat_message(f"Accepting file: {filename}", "system")
        
        def reject_file():
            # Send rejection
            if from_id in self.connected_users:
                response = json.dumps({
                    'type': 'file_reject',
                    'transfer_id': transfer_id
                })
                self.connected_users[from_id].send(response.encode('utf-8'))
            
            dialog.destroy()
            self.add_chat_message(f"Rejected file: {filename}", "system")
        
        accept_btn = tk.Button(
            button_frame,
            text="✓ Accept",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#4CAF50',
            command=accept_file,
            width=10
        )
        accept_btn.pack(side='left', padx=10)
        
        reject_btn = tk.Button(
            button_frame,
            text="✗ Reject",
            font=('Arial', 11),
            fg='white',
            bg='#F44336',
            command=reject_file,
            width=10
        )
        reject_btn.pack(side='left', padx=10)
        
        # Auto-reject after 30 seconds
        def auto_reject():
            if dialog.winfo_exists():
                reject_file()
        
        dialog.after(30000, auto_reject)
    
    def remove_connection(self, sock):
        """Remove a connection"""
        user_id_to_remove = None
        for user_id, user_sock in self.connected_users.items():
            if user_sock == sock:
                user_id_to_remove = user_id
                break
        
        if user_id_to_remove:
            del self.connected_users[user_id_to_remove]
            
            if user_id_to_remove in self.user_directory:
                self.user_directory[user_id_to_remove]['is_online'] = False
            
            self.root.after(0, self.update_contacts_list)
            self.root.after(0, self.add_chat_message,
                          f"User disconnected", "system")
        
        try:
            sock.close()
        except:
            pass
    
    def on_closing(self):
        """Clean shutdown"""
        self.messenger_active = False
        
        # Close all connections
        for sock in self.connected_users.values():
            try:
                sock.close()
            except:
                pass
        
        if self.messenger_server:
            try:
                self.messenger_server.close()
            except:
                pass
        
        if self.file_server:
            try:
                self.file_server.close()
            except:
                pass
        
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    # Hide console on Windows (only if not frozen as exe)
    if platform.system() == "Windows" and not getattr(sys, 'frozen', False):
        try:
            import ctypes
            whnd = ctypes.windll.kernel32.GetConsoleWindow()
            if whnd != 0:
                ctypes.windll.user32.ShowWindow(whnd, 0)
        except:
            pass
    
    app = LocalMessenger()
    app.run()

if __name__ == "__main__":
    main()
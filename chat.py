import tkinter as tk
from datetime import datetime
import os
import platform
import sys
import random
import threading
import time
import json
import socket
import select

class SimpleChatApp:
    def __init__(self):
        self.root = tk.Tk()
        
        # Window setup
        self.root.title("Simple Chat")
        self.root.geometry("400x500")
        self.root.configure(bg='#1a1a1a')
        
        # Chat state
        self.chat_active = False
        self.chat_server = None
        self.chat_clients = []
        
        # Chat settings
        self.my_name = f"User_{random.randint(1000, 9999)}"
        self.my_ip = self.get_local_ip()
        self.my_port = 12345
        self.connected_ips = []
        self.connected_names = {}
        self.message_queue = []
        
        # Configuration
        self.config_file = "chat_config.json"
        self.load_config()
        
        # Create chat interface
        self.create_chat_interface()
        
        # Start chat server
        self.start_chat_server()
        
        # Start checking for messages
        self.chat_thread_running = True
        threading.Thread(target=self.check_for_messages, daemon=True).start()
        
    def get_local_ip(self):
        """Get local IP address of the machine"""
        try:
            # Create a socket connection to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def load_config(self):
        """Load saved configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.my_name = config.get('username', self.my_name)
                    self.my_port = config.get('port', self.my_port)
                    self.connected_ips = config.get('connected_ips', [])
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'username': self.my_name,
                'port': self.my_port,
                'connected_ips': self.connected_ips
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def create_chat_interface(self):
        """Create the main chat interface"""
        # Title bar
        title_frame = tk.Frame(self.root, bg='#2a2a2a', height=40)
        title_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(
            title_frame,
            text="💬 Simple Chat",
            font=('Arial', 12, 'bold'),
            fg='#00BCD4',
            bg='#2a2a2a'
        ).pack(side='left', padx=10, pady=5)
        
        # Settings frame
        settings_frame = tk.Frame(self.root, bg='#1a1a1a')
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # Username
        tk.Label(
            settings_frame,
            text="Your Name:",
            font=('Arial', 9),
            fg='#AAAAAA',
            bg='#1a1a1a'
        ).pack(side='left')
        
        self.username_entry = tk.Entry(
            settings_frame,
            font=('Arial', 9),
            width=15,
            bg='#2a2a2a',
            fg='white',
            insertbackground='white'
        )
        self.username_entry.pack(side='left', padx=5)
        self.username_entry.insert(0, self.my_name)
        
        # Your IP display
        ip_frame = tk.Frame(settings_frame, bg='#1a1a1a')
        ip_frame.pack(side='left', padx=10)
        
        tk.Label(
            ip_frame,
            text="Your IPv4:",
            font=('Arial', 9),
            fg='#AAAAAA',
            bg='#1a1a1a'
        ).pack(side='left')
        
        tk.Label(
            ip_frame,
            text=self.my_ip,
            font=('Arial', 9, 'bold'),
            fg='#00FF00',
            bg='#1a1a1a'
        ).pack(side='left', padx=5)
        
        # Connect to others frame
        connect_frame = tk.Frame(self.root, bg='#1a1a1a')
        connect_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            connect_frame,
            text="Connect to IPv4 Address:",
            font=('Arial', 9),
            fg='#AAAAAA',
            bg='#1a1a1a'
        ).pack(side='left')
        
        self.connect_ip_entry = tk.Entry(
            connect_frame,
            font=('Arial', 9),
            width=15,
            bg='#2a2a2a',
            fg='white',
            insertbackground='white'
        )
        self.connect_ip_entry.pack(side='left', padx=5)
        
        self.connect_btn = tk.Button(
            connect_frame,
            text="Connect",
            font=('Arial', 9),
            fg='white',
            bg='#2196F3',
            command=self.connect_to_ip,
            width=8
        )
        self.connect_btn.pack(side='left', padx=5)
        
        # Disconnect button
        self.disconnect_btn = tk.Button(
            connect_frame,
            text="Disconnect All",
            font=('Arial', 9),
            fg='white',
            bg='#FF4444',
            command=self.disconnect_all,
            width=12
        )
        self.disconnect_btn.pack(side='left', padx=5)
        
        # Connected users frame
        users_frame = tk.Frame(self.root, bg='#1a1a1a')
        users_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            users_frame,
            text="Connected Users:",
            font=('Arial', 9),
            fg='#AAAAAA',
            bg='#1a1a1a'
        ).pack(side='left')
        
        self.users_listbox = tk.Listbox(
            users_frame,
            font=('Arial', 8),
            height=4,
            bg='#2a2a2a',
            fg='white',
            selectbackground='#3a3a3a'
        )
        self.users_listbox.pack(side='left', fill='x', expand=True, padx=(10, 0))
        self.update_users_list()
        
        # Chat display area
        chat_display_frame = tk.Frame(self.root, bg='#1a1a1a')
        chat_display_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Scrollbar for chat
        scrollbar = tk.Scrollbar(chat_display_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.chat_display = tk.Text(
            chat_display_frame,
            font=('Arial', 9),
            bg='#0a0a0a',
            fg='white',
            wrap='word',
            yscrollcommand=scrollbar.set,
            state='disabled',
            height=15
        )
        self.chat_display.pack(fill='both', expand=True)
        
        scrollbar.config(command=self.chat_display.yview)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Ready to chat! Share your IPv4 Address with others to connect.",
            font=('Arial', 8),
            fg='#FF8800',
            bg='#1a1a1a'
        )
        self.status_label.pack(pady=(0, 5))
        
        # Message input area
        input_frame = tk.Frame(self.root, bg='#1a1a1a')
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.message_entry = tk.Entry(
            input_frame,
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='white',
            insertbackground='white'
        )
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_btn = tk.Button(
            input_frame,
            text="Send",
            font=('Arial', 9, 'bold'),
            fg='white',
            bg='#0088cc',
            command=self.send_message,
            width=8
        )
        self.send_btn.pack(side='right')
        
        # Add welcome message
        self.add_chat_message("Welcome to Simple Chat!", "system")
        self.add_chat_message(f"Your IP: {self.my_ip}", "system")
        self.add_chat_message(f"Share this IP with others to connect", "system")
        
    def start_chat_server(self):
        """Start the chat server to listen for incoming connections"""
        try:
            self.chat_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.chat_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.chat_server.bind(('0.0.0.0', self.my_port))
            self.chat_server.listen(5)
            self.chat_server.setblocking(False)
            self.add_chat_message(f"Chat server started on port {self.my_port}", "system")
        except Exception as e:
            self.add_chat_message(f"Error starting server: {e}", "system")
    
    def connect_to_ip(self):
        """Connect to another user's IP"""
        ip = self.connect_ip_entry.get().strip()
        if not ip:
            self.status_label.config(text="✗ Please enter an IPv4 address", fg='#FF0000')
            return
        
        if ip == self.my_ip:
            self.status_label.config(text="✗ Cannot connect to yourself", fg='#FF0000')
            return
        
        if ip in self.connected_ips:
            self.status_label.config(text="✓ Already connected", fg='#00FF00')
            return
        
        # Try to connect
        threading.Thread(target=self.connect_to_ip_thread, args=(ip,), daemon=True).start()
    
    def connect_to_ip_thread(self, ip):
        """Thread for connecting to IP"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((ip, self.my_port))  # Try their port
            client_socket.setblocking(False)
            
            # Send our username
            connect_msg = json.dumps({
                'type': 'connect',
                'name': self.my_name,
                'ip': self.my_ip
            })
            client_socket.send(connect_msg.encode('utf-8'))
            
            # Add to connected clients
            self.chat_clients.append(client_socket)
            self.connected_ips.append(ip)
            self.connected_names[ip] = f"User_{ip}"
            
            self.root.after(0, self.status_label.config, 
                          {"text": f"✓ Connected to {ip}", "fg": '#00FF00'})
            self.root.after(0, self.update_users_list)
            self.root.after(0, self.add_chat_message, 
                          f"Connected to {ip}", "system")
            
        except Exception as e:
            self.root.after(0, self.status_label.config,
                          {"text": f"✗ Failed to connect: {str(e)}", "fg": '#FF0000'})
    
    def disconnect_all(self):
        """Disconnect from all users"""
        for client in self.chat_clients:
            try:
                client.close()
            except:
                pass
        
        self.chat_clients.clear()
        self.connected_ips.clear()
        self.connected_names.clear()
        
        self.update_users_list()
        self.add_chat_message("Disconnected from all users", "system")
        self.status_label.config(text="Disconnected from all users", fg='#FF8800')
    
    def update_users_list(self):
        """Update the list of connected users"""
        self.users_listbox.delete(0, tk.END)
        
        # Add yourself
        self.users_listbox.insert(tk.END, f"You: {self.my_name} ({self.my_ip})")
        
        # Add connected users
        for ip in self.connected_ips:
            name = self.connected_names.get(ip, f"User_{ip}")
            self.users_listbox.insert(tk.END, f"{name} ({ip})")
    
    def add_chat_message(self, message, sender="system"):
        """Add a message to the chat display"""
        self.chat_display.config(state='normal')
        
        # Configure tags for different senders
        if not self.chat_display.tag_names():
            self.chat_display.tag_config("you", foreground="#0088cc", font=('Arial', 9, 'bold'))
            self.chat_display.tag_config("other", foreground="#00aa00", font=('Arial', 9, 'bold'))
            self.chat_display.tag_config("system", foreground="#ff8800", font=('Arial', 9, 'italic'))
            self.chat_display.tag_config("timestamp", foreground="#666666", font=('Arial', 8))
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Insert timestamp and message at the END
        self.chat_display.insert('end', f"[{timestamp}] ", "timestamp")
        
        # Determine tag based on sender
        if sender == "you":
            tag = "you"
            display_msg = f"You: {message}"
        elif sender == "system":
            tag = "system"
            display_msg = message
        else:
            tag = "other"
            display_msg = f"{sender}: {message}"
        
        self.chat_display.insert('end', f"{display_msg}\n", tag)
        
        # Keep only last 100 messages
        lines = self.chat_display.get('1.0', 'end').split('\n')
        if len(lines) > 200:  # 100 messages * 2 lines each
            self.chat_display.delete('1.0', f'{len(lines)-200}.0')
        
        self.chat_display.config(state='disabled')
        self.chat_display.see('end')  # Scroll to end
    
    def send_message(self, event=None):
        """Send a message to all connected users"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Update username if changed
        new_name = self.username_entry.get().strip()
        if new_name and new_name != self.my_name:
            self.my_name = new_name
            self.save_config()
            self.update_users_list()
        
        # Clear input
        self.message_entry.delete(0, tk.END)
        
        # Show message in chat
        self.add_chat_message(message, "you")
        
        # Send to all connected users
        if self.chat_clients:
            threading.Thread(target=self.send_to_all, args=(message,), daemon=True).start()
        else:
            self.add_chat_message("No one is connected to receive your message", "system")
    
    def send_to_all(self, message):
        """Send message to all connected users"""
        disconnect_list = []
        
        for client in self.chat_clients:
            try:
                msg_data = json.dumps({
                    'type': 'message',
                    'name': self.my_name,
                    'message': message,
                    'ip': self.my_ip
                })
                client.send(msg_data.encode('utf-8'))
            except Exception as e:
                disconnect_list.append(client)
        
        # Remove disconnected clients
        for client in disconnect_list:
            self.remove_client(client)
    
    def remove_client(self, client):
        """Remove a disconnected client"""
        try:
            client.close()
            self.chat_clients.remove(client)
            
            # Find IP to remove from connected lists
            for ip, sock in list(self.connected_names.items()):
                # We don't have direct mapping, so we'll update list when we detect disconnection
                pass
            
            self.root.after(0, self.update_users_list)
        except:
            pass
    
    def check_for_messages(self):
        """Check for incoming messages and connections"""
        while self.chat_thread_running:
            try:
                # Check for new connections
                readable, _, _ = select.select([self.chat_server] + self.chat_clients, [], [], 0.1)
                
                for sock in readable:
                    if sock == self.chat_server:
                        # New connection
                        client_socket, client_address = self.chat_server.accept()
                        client_socket.setblocking(False)
                        self.chat_clients.append(client_socket)
                        self.root.after(0, self.add_chat_message, 
                                      f"New connection from {client_address[0]}", "system")
                    else:
                        # Message from existing client
                        try:
                            data = sock.recv(1024).decode('utf-8')
                            if data:
                                self.process_incoming_message(data, sock)
                            else:
                                # Client disconnected
                                self.remove_client(sock)
                        except:
                            # Client disconnected
                            self.remove_client(sock)
                
            except Exception as e:
                time.sleep(0.1)
    
    def process_incoming_message(self, data, sock):
        """Process incoming message"""
        try:
            message_data = json.loads(data)
            msg_type = message_data.get('type')
            
            if msg_type == 'connect':
                # New user connecting
                name = message_data.get('name', 'Unknown')
                ip = message_data.get('ip', '0.0.0.0')
                
                if ip not in self.connected_ips and ip != self.my_ip:
                    self.connected_ips.append(ip)
                    self.connected_names[ip] = name
                    
                    self.root.after(0, self.update_users_list)
                    self.root.after(0, self.add_chat_message,
                                  f"{name} ({ip}) connected", "system")
            
            elif msg_type == 'message':
                # Regular message
                name = message_data.get('name', 'Unknown')
                message = message_data.get('message', '')
                ip = message_data.get('ip', '0.0.0.0')
                
                # Update name if we have it
                if ip in self.connected_names and self.connected_names[ip] != name:
                    self.connected_names[ip] = name
                    self.root.after(0, self.update_users_list)
                
                self.root.after(0, self.add_chat_message, message, name)
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def on_closing(self):
        """Clean up when closing"""
        self.chat_thread_running = False
        
        # Close all connections
        if self.chat_server:
            self.chat_server.close()
        
        for client in self.chat_clients:
            try:
                client.close()
            except:
                pass
        
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    # Hide console window on Windows (optional)
    if platform.system() == "Windows":
        try:
            import ctypes
            whnd = ctypes.windll.kernel32.GetConsoleWindow()
            if whnd != 0:
                ctypes.windll.user32.ShowWindow(whnd, 0)
        except:
            pass
    
    app = SimpleChatApp()
    app.run()

if __name__ == "__main__":
    main()
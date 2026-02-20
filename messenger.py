import tkinter as tk
from tkinter import font as tkfont, ttk, messagebox, filedialog
import datetime
import random
import hashlib
import os
import json
import time
import threading
import socket
import pickle
from pathlib import Path
import shutil

class TelegramStyleMessenger:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Operation")
        self.root.geometry("900x650")
        self.root.configure(bg='#0f0f0f')
        
        # User data
        self.display_name = ""
        self.username = ""
        self.phone = ""
        self.user_id = ""
        self.is_logged_in = False
        self.profile_photo = None
        self.bio = ""
        
        # Menu state
        self.menu_visible = False
        self.menu_window = None
        
        # Settings state
        self.night_mode = True
        self.notifications = True
        self.auto_download = True
        self.theme_color = "#4a6da8"
        
        # Data structures
        self.chats = []
        self.contacts = []
        self.messages = {}  # {chat_id: [messages]}
        self.current_chat_index = None
        self.current_chat_id = None
        self.archived_chats = []
        
        # Network
        self.server = None
        self.is_online = False
        self.online_users = {}
        
        # File paths
        self.data_dir = os.path.join(os.path.expanduser("~"), ".telegram_clone")
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Telegram")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Load saved data
        self.load_user_data()
        self.load_chats()
        self.load_contacts()
        self.load_messages()
        
        # Start network services
        self.start_network_services()
        
        # Setup UI
        if self.is_logged_in:
            self.setup_main_ui()
        else:
            self.show_login_screen()
    
    # ==================== DATA MANAGEMENT ====================
    
    def load_user_data(self):
        """Load saved user data"""
        user_file = os.path.join(self.data_dir, "user.json")
        if os.path.exists(user_file):
            try:
                with open(user_file, 'r') as f:
                    data = json.load(f)
                    self.display_name = data.get('display_name', '')
                    self.username = data.get('username', '')
                    self.phone = data.get('phone', '')
                    self.user_id = data.get('user_id', '')
                    self.bio = data.get('bio', '')
                    self.theme_color = data.get('theme_color', '#4a6da8')
                    self.notifications = data.get('notifications', True)
                    self.auto_download = data.get('auto_download', True)
                    self.is_logged_in = True
                    
                # Load profile photo if exists
                photo_path = os.path.join(self.data_dir, "profile_photo.png")
                if os.path.exists(photo_path):
                    self.profile_photo = photo_path
            except:
                pass
    
    def save_user_data(self):
        """Save user data"""
        user_file = os.path.join(self.data_dir, "user.json")
        with open(user_file, 'w') as f:
            json.dump({
                'display_name': self.display_name,
                'username': self.username,
                'phone': self.phone,
                'user_id': self.user_id,
                'bio': self.bio,
                'theme_color': self.theme_color,
                'notifications': self.notifications,
                'auto_download': self.auto_download
            }, f)
    
    def load_chats(self):
        """Load saved chats"""
        chats_file = os.path.join(self.data_dir, "chats.json")
        if os.path.exists(chats_file):
            try:
                with open(chats_file, 'r') as f:
                    self.chats = json.load(f)
            except:
                self.chats = []
    
    def save_chats(self):
        """Save chats"""
        chats_file = os.path.join(self.data_dir, "chats.json")
        with open(chats_file, 'w') as f:
            json.dump(self.chats, f)
    
    def load_contacts(self):
        """Load saved contacts"""
        contacts_file = os.path.join(self.data_dir, "contacts.json")
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r') as f:
                    self.contacts = json.load(f)
            except:
                self.contacts = []
    
    def save_contacts(self):
        """Save contacts"""
        contacts_file = os.path.join(self.data_dir, "contacts.json")
        with open(contacts_file, 'w') as f:
            json.dump(self.contacts, f)
    
    def load_messages(self):
        """Load saved messages"""
        messages_file = os.path.join(self.data_dir, "messages.pkl")
        if os.path.exists(messages_file):
            try:
                with open(messages_file, 'rb') as f:
                    self.messages = pickle.load(f)
            except:
                self.messages = {}
    
    def save_messages(self):
        """Save messages"""
        messages_file = os.path.join(self.data_dir, "messages.pkl")
        with open(messages_file, 'wb') as f:
            pickle.dump(self.messages, f)
    
    # ==================== NETWORK SERVICES ====================
    
    def start_network_services(self):
        """Start network services for messaging"""
        def server_thread():
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.server.bind(('0.0.0.0', 8888))
                self.server.listen(5)
                self.is_online = True
                
                while self.is_online:
                    client, addr = self.server.accept()
                    threading.Thread(target=self.handle_client, args=(client, addr)).start()
            except:
                pass
        
        threading.Thread(target=server_thread, daemon=True).start()
    
    def handle_client(self, client, addr):
        """Handle incoming client connection"""
        try:
            data = client.recv(4096)
            if data:
                message = json.loads(data.decode())
                msg_type = message.get('type')
                
                if msg_type == 'message':
                    self.receive_message(message)
                elif msg_type == 'file':
                    self.receive_file(message, client)
                elif msg_type == 'typing':
                    self.show_typing_indicator(message)
                elif msg_type == 'read':
                    self.mark_as_read(message)
        except:
            pass
        finally:
            client.close()
    
    def send_message_network(self, to_user, text):
        """Send message over network"""
        try:
            # In real implementation, would need to know recipient's IP
            # For demo, we'll simulate
            pass
        except:
            pass
    
    def receive_message(self, message):
        """Receive message from network"""
        from_id = message.get('from_id')
        from_name = message.get('from_name')
        text = message.get('text')
        timestamp = message.get('timestamp', time.time())
        
        # Find or create chat
        chat_id = None
        for i, chat in enumerate(self.chats):
            if chat.get('id') == from_id:
                chat_id = i
                break
        
        if chat_id is None:
            # Add new chat
            chat_data = {
                'id': from_id,
                'name': from_name,
                'last_message': text,
                'time': self.format_timestamp(timestamp),
                'avatar': self.get_random_avatar(),
                'color': self.get_random_color(),
                'unread': 1
            }
            self.chats.append(chat_data)
            chat_id = len(self.chats) - 1
            self.root.after(0, self.refresh_chat_list)
        
        # Save message
        if from_id not in self.messages:
            self.messages[from_id] = []
        
        self.messages[from_id].append({
            'text': text,
            'sent': False,
            'time': timestamp,
            'sender': from_name
        })
        
        # Update last message
        self.chats[chat_id]['last_message'] = text
        self.chats[chat_id]['time'] = self.format_timestamp(timestamp)
        if 'unread' in self.chats[chat_id]:
            self.chats[chat_id]['unread'] += 1
        else:
            self.chats[chat_id]['unread'] = 1
        
        self.save_messages()
        self.save_chats()
        
        # Show notification
        if chat_id != self.current_chat_index:
            self.root.after(0, lambda: self.show_notification(from_name, text))
        
        self.root.after(0, self.refresh_chat_list)
    
    def show_notification(self, name, text):
        """Show desktop notification"""
        # In real implementation, would use system notifications
        print(f"New message from {name}: {text}")
    
    def format_timestamp(self, ts):
        """Format timestamp for display"""
        dt = datetime.datetime.fromtimestamp(ts)
        now = datetime.datetime.now()
        
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        elif (now - dt).days < 7:
            return dt.strftime("%A")[:3]
        else:
            return dt.strftime("%m/%d")
    
    # ==================== LOGIN SCREEN ====================
    
    def show_login_screen(self):
        """Show the initial login/registration screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg='#0f0f0f')
        main_frame.pack(expand=True, fill='both')
        
        # Center content
        center_frame = tk.Frame(main_frame, bg='#0f0f0f')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Logo
        logo_label = tk.Label(center_frame, text="📱", bg='#0f0f0f', fg=self.theme_color,
                             font=('Arial', 64))
        logo_label.pack(pady=(0, 20))
        
        # Title
        title_label = tk.Label(center_frame, text="Welcome to Telegram", bg='#0f0f0f', fg='white',
                              font=('Arial', 24, 'bold'))
        title_label.pack(pady=(0, 30))
        
        # Form frame
        form_frame = tk.Frame(center_frame, bg='#1f1f1f', padx=40, pady=30)
        form_frame.pack()
        
        # Display Name
        tk.Label(form_frame, text="Display Name", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        self.name_entry = tk.Entry(form_frame, bg='#2f2f2f', fg='white',
                                   insertbackground='white', font=('Arial', 12),
                                   width=30, bd=0, highlightthickness=1,
                                   highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        self.name_entry.pack(pady=(0, 15))
        self.name_entry.focus_set()
        
        # Username
        tk.Label(form_frame, text="Username", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        self.username_entry = tk.Entry(form_frame, bg='#2f2f2f', fg='white',
                                      insertbackground='white', font=('Arial', 12),
                                      width=30, bd=0, highlightthickness=1,
                                      highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        self.username_entry.pack(pady=(0, 15))
        
        # Phone
        tk.Label(form_frame, text="Phone Number", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        self.phone_entry = tk.Entry(form_frame, bg='#2f2f2f', fg='white',
                                   insertbackground='white', font=('Arial', 12),
                                   width=30, bd=0, highlightthickness=1,
                                   highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        self.phone_entry.pack(pady=(0, 20))
        
        # Start button
        start_btn = tk.Button(form_frame, text="Start Messaging", bg=self.theme_color, fg='white',
                             font=('Arial', 12, 'bold'), padx=30, pady=10,
                             command=self.complete_login)
        start_btn.pack()
    
    def complete_login(self):
        """Complete the login process"""
        display_name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        phone = self.phone_entry.get().strip()
        
        if not display_name:
            messagebox.showerror("Error", "Please enter your display name")
            return
        
        if not username:
            # Generate a username from display name
            username = display_name.lower().replace(' ', '_') + str(random.randint(100, 999))
        
        # Generate unique user ID
        unique_string = f"{display_name}_{username}_{datetime.datetime.now().isoformat()}_{random.randint(1000, 9999)}"
        self.user_id = hashlib.md5(unique_string.encode()).hexdigest()[:16]
        
        self.display_name = display_name
        self.username = username
        self.phone = phone
        self.is_logged_in = True
        
        # Save user data
        self.save_user_data()
        
        # Add saved messages chat
        self.chats.append({
            'id': 'saved',
            'name': 'Saved Messages',
            'last_message': 'Your notes and media',
            'time': 'now',
            'avatar': '📌',
            'color': '#fbc02d',
            'pinned': True
        })
        
        self.save_chats()
        
        # Setup main UI
        self.setup_main_ui()
    
    # ==================== MAIN UI ====================
    
    def setup_main_ui(self):
        """Setup the main UI after login"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = tk.Frame(self.root, bg='#0f0f0f')
        main_container.pack(fill='both', expand=True)
        
        # Left panel - Chat list
        left_panel = tk.Frame(main_container, bg='#1f1f1f', width=350)
        left_panel.pack(side='left', fill='y')
        left_panel.pack_propagate(False)
        
        # Right panel - Chat area
        self.right_panel = tk.Frame(main_container, bg='#0f0f0f')
        self.right_panel.pack(side='right', fill='both', expand=True)
        
        # ========== LEFT PANEL ==========
        
        # Top bar
        top_bar = tk.Frame(left_panel, bg='#1f1f1f', height=60)
        top_bar.pack(fill='x')
        top_bar.pack_propagate(False)
        
        # Menu button
        menu_btn = tk.Button(top_bar, text="☰", bg='#1f1f1f', fg='white',
                            font=('Arial', 16), bd=0, activebackground='#2f2f2f',
                            cursor='hand2', command=self.toggle_menu)
        menu_btn.pack(side='left', padx=15, pady=15)
        
        # Search bar
        search_frame = tk.Frame(top_bar, bg='#2f2f2f', height=36)
        search_frame.pack(side='left', fill='x', expand=True, padx=5, pady=12)
        search_frame.pack_propagate(False)
        
        search_icon = tk.Label(search_frame, text="🔍", bg='#2f2f2f', fg='#888',
                              font=('Arial', 12))
        search_icon.pack(side='left', padx=(10, 5))
        
        self.search_entry = tk.Entry(search_frame, bg='#2f2f2f', fg='white',
                                     insertbackground='white', font=('Arial', 12),
                                     bd=0, highlightthickness=0)
        self.search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.search_entry.insert(0, "Search")
        self.search_entry.bind('<FocusIn>', self.clear_search_placeholder)
        self.search_entry.bind('<FocusOut>', self.restore_search_placeholder)
        self.search_entry.bind('<KeyRelease>', self.search_chats)
        
        # Profile button
        profile_btn = tk.Button(top_bar, text="👤", bg='#1f1f1f', fg='white',
                               font=('Arial', 16), bd=0, activebackground='#2f2f2f',
                               cursor='hand2', command=self.open_profile)
        profile_btn.pack(side='right', padx=15, pady=15)
        
        # Chat tabs
        tab_frame = tk.Frame(left_panel, bg='#1f1f1f', height=40)
        tab_frame.pack(fill='x')
        tab_frame.pack_propagate(False)
        
        self.chats_tab = tk.Button(tab_frame, text="Chats", bg='#2f2f2f', fg='white',
                                  font=('Arial', 11), bd=0, command=self.show_chats)
        self.chats_tab.pack(side='left', fill='both', expand=True)
        
        self.contacts_tab = tk.Button(tab_frame, text="Contacts", bg='#1f1f1f', fg='#888',
                                     font=('Arial', 11), bd=0, command=self.show_contacts)
        self.contacts_tab.pack(side='left', fill='both', expand=True)
        
        # Chat list container
        self.chat_container = tk.Frame(left_panel, bg='#1f1f1f')
        self.chat_container.pack(fill='both', expand=True)
        
        # Create scrollable chat list
        self.create_chat_list()
        
        # Show empty chat area
        self.show_empty_chat()
    
    def create_chat_list(self):
        """Create scrollable chat list"""
        # Clear container
        for widget in self.chat_container.winfo_children():
            widget.destroy()
        
        # Canvas for scrolling
        canvas = tk.Canvas(self.chat_container, bg='#1f1f1f', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.chat_container, orient='vertical', command=canvas.yview)
        self.chat_scrollable = tk.Frame(canvas, bg='#1f1f1f')
        
        self.chat_scrollable.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=self.chat_scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind mouse wheel
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))
        
        # Populate chats
        self.refresh_chat_list()
    
    def refresh_chat_list(self):
        """Refresh the chat list display"""
        # Clear existing
        for widget in self.chat_scrollable.winfo_children():
            widget.destroy()
        
        # Add archived chats if any
        if self.archived_chats:
            archive_frame = tk.Frame(self.chat_scrollable, bg='#1f1f1f')
            archive_frame.pack(fill='x', pady=1)
            
            archive_btn = tk.Button(archive_frame, text="📁 Archived Chats", bg='#1f1f1f', fg='#888',
                                   font=('Arial', 12), anchor='w', padx=20, pady=10,
                                   command=self.show_archived)
            archive_btn.pack(fill='x')
        
        # Separate saved messages from other chats
        saved_chat = None
        other_chats = []
        for chat in self.chats:
            if chat.get('id') == 'saved':
                saved_chat = chat
            else:
                other_chats.append(chat)
        
        # Always show saved messages first
        if saved_chat:
            self.render_chat_item(saved_chat, pinned=True)
        
        # Show pinned chats (excluding saved)
        pinned = [c for c in other_chats if c.get('pinned')]
        for chat in pinned:
            self.render_chat_item(chat, pinned=True)
        
        # Show regular chats
        regular = [c for c in other_chats if not c.get('pinned')]
        for chat in regular:
            self.render_chat_item(chat)
    
    def render_chat_item(self, chat, pinned=False):
        """Render a single chat item"""
        frame = tk.Frame(self.chat_scrollable, bg='#1f1f1f', height=70)
        frame.pack(fill='x', pady=1)
        frame.pack_propagate(False)
        
        # Store chat ID
        frame.chat_id = chat.get('id')
        
        # Bind click
        frame.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        # Avatar
        avatar = tk.Frame(frame, bg=chat['color'], width=50, height=50)
        avatar.pack(side='left', padx=(15, 10), pady=10)
        avatar.pack_propagate(False)
        
        avatar_label = tk.Label(avatar, text=chat['avatar'], bg=chat['color'],
                               fg='white', font=('Arial', 20))
        avatar_label.pack(expand=True)
        avatar_label.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        # Info
        info = tk.Frame(frame, bg='#1f1f1f')
        info.pack(side='left', fill='both', expand=True, pady=10)
        info.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        # Top row
        top = tk.Frame(info, bg='#1f1f1f')
        top.pack(fill='x')
        top.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        name = tk.Label(top, text=chat['name'], bg='#1f1f1f', fg='white',
                       font=('Arial', 13, 'bold'))
        name.pack(side='left')
        name.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        time = tk.Label(top, text=chat['time'], bg='#1f1f1f', fg='#888',
                       font=('Arial', 11))
        time.pack(side='right', padx=(0, 15))
        time.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        # Bottom row
        bottom = tk.Frame(info, bg='#1f1f1f')
        bottom.pack(fill='x', pady=(2, 0))
        bottom.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        # Pin icon if pinned
        if pinned:
            pin = tk.Label(bottom, text="📌", bg='#1f1f1f', fg='#888',
                          font=('Arial', 11))
            pin.pack(side='left', padx=(0, 3))
            pin.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        # Last message
        last = tk.Label(bottom, text=chat['last_message'], bg='#1f1f1f', fg='#888',
                       font=('Arial', 11), anchor='w')
        last.pack(side='left', fill='x', expand=True)
        last.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
        
        # Unread count
        if chat.get('unread', 0) > 0:
            unread = tk.Frame(bottom, bg='#4CAF50', width=20, height=20)
            unread.pack(side='right', padx=(0, 15))
            unread.pack_propagate(False)
            
            unread_label = tk.Label(unread, text=str(chat['unread']), bg='#4CAF50',
                                   fg='white', font=('Arial', 10, 'bold'))
            unread_label.pack(expand=True)
            unread_label.bind('<Button-1>', lambda e, c=chat: self.open_chat(c))
    
    def show_empty_chat(self):
        """Show empty chat area"""
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        center = tk.Frame(self.right_panel, bg='#0f0f0f')
        center.pack(expand=True)
        
        logo = tk.Label(center, text="📱", bg='#0f0f0f', fg='#2f2f2f',
                       font=('Arial', 48))
        logo.pack(pady=(0, 10))
        
        welcome = tk.Label(center, text=f"Welcome, {self.display_name}!",
                          bg='#0f0f0f', fg='white', font=('Arial', 18, 'bold'))
        welcome.pack(pady=(0, 5))
        
        select = tk.Label(center, text="Select a chat to start messaging",
                         bg='#0f0f0f', fg='#888', font=('Arial', 16))
        select.pack()
    
    def open_chat(self, chat):
        """Open a chat"""
        # Find index
        for i, c in enumerate(self.chats):
            if c.get('id') == chat.get('id'):
                self.current_chat_index = i
                self.current_chat_id = chat.get('id')
                break
        
        # Reset unread
        if chat.get('unread', 0) > 0:
            chat['unread'] = 0
            self.save_chats()
        
        # Show chat interface
        self.show_chat_interface(chat)
    
    def show_chat_interface(self, chat):
        """Show the chat interface"""
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        # Header
        header = tk.Frame(self.right_panel, bg='#1f1f1f', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Back button (mobile style)
        back_btn = tk.Button(header, text="←", bg='#1f1f1f', fg='white',
                            font=('Arial', 16), bd=0, command=self.show_empty_chat)
        back_btn.pack(side='left', padx=10, pady=15)
        
        # Avatar
        avatar = tk.Frame(header, bg=chat['color'], width=40, height=40)
        avatar.pack(side='left', padx=5, pady=10)
        avatar.pack_propagate(False)
        
        tk.Label(avatar, text=chat['avatar'], bg=chat['color'],
                fg='white', font=('Arial', 16)).pack(expand=True)
        
        # Name and status
        name_status = tk.Frame(header, bg='#1f1f1f')
        name_status.pack(side='left', fill='both', expand=True, pady=10)
        
        tk.Label(name_status, text=chat['name'], bg='#1f1f1f', fg='white',
                font=('Arial', 14, 'bold')).pack(anchor='w')
        
        # Status
        if chat.get('id') == 'saved':
            status = "Your cloud storage"
            status_color = '#888'
        else:
            status = "online" if random.random() > 0.5 else "last seen recently"
            status_color = '#4CAF50' if status == "online" else '#888'
        
        tk.Label(name_status, text=status, bg='#1f1f1f', fg=status_color,
                font=('Arial', 10)).pack(anchor='w')
        
        # Call buttons (not for saved messages)
        if chat.get('id') != 'saved':
            call_frame = tk.Frame(header, bg='#1f1f1f')
            call_frame.pack(side='right', padx=10)
            
            tk.Button(call_frame, text="📞", bg='#1f1f1f', fg='white',
                     font=('Arial', 14), bd=0).pack(side='left', padx=5)
            tk.Button(call_frame, text="📹", bg='#1f1f1f', fg='white',
                     font=('Arial', 14), bd=0).pack(side='left', padx=5)
        
        # Menu button
        menu_btn = tk.Button(header, text="⋮", bg='#1f1f1f', fg='white',
                            font=('Arial', 16), bd=0,
                            command=lambda: self.show_chat_menu(chat))
        menu_btn.pack(side='right', padx=10)
        
        # Messages area
        messages_frame = tk.Frame(self.right_panel, bg='#0f0f0f')
        messages_frame.pack(fill='both', expand=True)
        
        # Canvas for scrolling messages
        canvas = tk.Canvas(messages_frame, bg='#0f0f0f', highlightthickness=0)
        scrollbar = tk.Scrollbar(messages_frame, orient='vertical', command=canvas.yview)
        self.messages_scrollable = tk.Frame(canvas, bg='#0f0f0f')
        
        self.messages_scrollable.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=self.messages_scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))
        
        # Load messages
        self.load_messages_display(chat)
        
        # Input area
        input_frame = tk.Frame(self.right_panel, bg='#1f1f1f', height=70)
        input_frame.pack(fill='x', side='bottom')
        input_frame.pack_propagate(False)
        
        # Attach button
        attach_btn = tk.Button(input_frame, text="📎", bg='#1f1f1f', fg='white',
                              font=('Arial', 16), bd=0, command=lambda: self.attach_file(chat))
        attach_btn.pack(side='left', padx=10, pady=20)
        
        # Emoji button
        emoji_btn = tk.Button(input_frame, text="😊", bg='#1f1f1f', fg='white',
                             font=('Arial', 16), bd=0, command=self.show_emoji_picker)
        emoji_btn.pack(side='left', padx=5, pady=20)
        
        # Message entry
        self.message_entry = tk.Text(input_frame, bg='#2f2f2f', fg='white',
                                     insertbackground='white', font=('Arial', 12),
                                     height=2, width=50, bd=0, wrap='word')
        self.message_entry.pack(side='left', fill='both', expand=True, padx=5, pady=15)
        self.message_entry.bind('<Return>', lambda e: self.send_message(chat))
        self.message_entry.bind('<Shift-Return>', lambda e: None)
        
        # Send button
        send_btn = tk.Button(input_frame, text="📤", bg='#1f1f1f', fg='white',
                            font=('Arial', 16), bd=0, command=lambda: self.send_message(chat))
        send_btn.pack(side='right', padx=15, pady=20)
    
    def load_messages_display(self, chat):
        """Load and display messages"""
        chat_id = chat.get('id')
        if chat_id in self.messages:
            for msg in self.messages[chat_id]:
                self.display_message(msg, chat)
    
    def display_message(self, msg, chat):
        """Display a single message"""
        frame = tk.Frame(self.messages_scrollable, bg='#0f0f0f')
        frame.pack(fill='x', pady=2, padx=10)
        
        if msg['sent']:
            # Sent message (right)
            bubble = tk.Frame(frame, bg='#005c4b')
            bubble.pack(side='right')
            
            # Message text
            text = tk.Label(bubble, text=msg['text'], bg='#005c4b', fg='white',
                           font=('Arial', 11), wraplength=300, justify='left',
                           padx=10, pady=5)
            text.pack()
            
            # Time
            time_str = datetime.datetime.fromtimestamp(msg['time']).strftime("%H:%M")
            time_label = tk.Label(bubble, text=time_str, bg='#005c4b', fg='#aaa',
                                 font=('Arial', 8))
            time_label.pack(anchor='e', padx=5, pady=(0, 2))
        else:
            # Received message (left)
            bubble = tk.Frame(frame, bg='#1f1f1f')
            bubble.pack(side='left')
            
            # Sender name for groups
            if chat.get('is_group'):
                sender = tk.Label(bubble, text=msg.get('sender', ''), bg='#1f1f1f', fg=self.theme_color,
                                 font=('Arial', 10, 'bold'))
                sender.pack(anchor='w', padx=10, pady=(5, 0))
            
            # Message text
            text = tk.Label(bubble, text=msg['text'], bg='#1f1f1f', fg='white',
                           font=('Arial', 11), wraplength=300, justify='left',
                           padx=10, pady=5)
            text.pack()
            
            # Time
            time_str = datetime.datetime.fromtimestamp(msg['time']).strftime("%H:%M")
            time_label = tk.Label(bubble, text=time_str, bg='#1f1f1f', fg='#aaa',
                                 font=('Arial', 8))
            time_label.pack(anchor='e', padx=5, pady=(0, 2))
    
    def send_message(self, chat):
        """Send a message"""
        text = self.message_entry.get('1.0', 'end-1c').strip()
        if not text:
            return
        
        # Clear input
        self.message_entry.delete('1.0', tk.END)
        
        # Create message
        timestamp = time.time()
        msg = {
            'text': text,
            'sent': True,
            'time': timestamp,
            'sender': self.display_name
        }
        
        # Save message
        chat_id = chat.get('id')
        if chat_id not in self.messages:
            self.messages[chat_id] = []
        
        self.messages[chat_id].append(msg)
        self.save_messages()
        
        # Display message
        self.display_message(msg, chat)
        
        # Update chat list
        for i, c in enumerate(self.chats):
            if c.get('id') == chat_id:
                self.chats[i]['last_message'] = text
                self.chats[i]['time'] = self.format_timestamp(timestamp)
                break
        
        self.save_chats()
        self.refresh_chat_list()
        
        # Scroll to bottom
        self.messages_scrollable.update_idletasks()
        self.messages_scrollable.master.yview_moveto(1.0)
        
        # Simulate reply after delay (for demo)
        if chat_id != 'saved':
            self.root.after(2000, lambda: self.simulate_reply(chat))
    
    def simulate_reply(self, chat):
        """Simulate a reply (for demo)"""
        replies = [
            "👍",
            "Thanks!",
            "😊",
            "Got it",
            "Sounds good",
            "OK",
            "👋",
            "I'll check later"
        ]
        
        timestamp = time.time()
        msg = {
            'text': random.choice(replies),
            'sent': False,
            'time': timestamp,
            'sender': chat['name']
        }
        
        chat_id = chat.get('id')
        self.messages[chat_id].append(msg)
        self.save_messages()
        
        self.display_message(msg, chat)
        
        # Update unread count if chat not open
        if chat_id != self.current_chat_id:
            for i, c in enumerate(self.chats):
                if c.get('id') == chat_id:
                    self.chats[i]['unread'] = self.chats[i].get('unread', 0) + 1
                    self.chats[i]['last_message'] = msg['text']
                    self.chats[i]['time'] = self.format_timestamp(timestamp)
                    break
            
            self.save_chats()
            self.refresh_chat_list()
    
    def attach_file(self, chat):
        """Attach and send a file"""
        filename = filedialog.askopenfilename()
        if not filename:
            return
        
        # Copy file to downloads
        basename = os.path.basename(filename)
        dest = os.path.join(self.download_dir, f"{int(time.time())}_{basename}")
        shutil.copy2(filename, dest)
        
        # Send as message
        filesize = os.path.getsize(filename)
        if filesize < 1024 * 1024:
            size_str = f"{filesize/1024:.1f} KB"
        else:
            size_str = f"{filesize/(1024*1024):.1f} MB"
        
        msg_text = f"📎 File: {basename} ({size_str})"
        
        timestamp = time.time()
        msg = {
            'text': msg_text,
            'sent': True,
            'time': timestamp,
            'file': dest
        }
        
        chat_id = chat.get('id')
        if chat_id not in self.messages:
            self.messages[chat_id] = []
        
        self.messages[chat_id].append(msg)
        self.save_messages()
        
        self.display_message(msg, chat)
        
        # Update chat list
        for i, c in enumerate(self.chats):
            if c.get('id') == chat_id:
                self.chats[i]['last_message'] = msg_text
                self.chats[i]['time'] = self.format_timestamp(timestamp)
                break
        
        self.save_chats()
        self.refresh_chat_list()
    
    def show_emoji_picker(self):
        """Show emoji picker (simplified)"""
        emojis = "😊😂❤️👍🔥🎉😢😡🤔😴🥳😎👋🙏💯"
        pos = self.message_entry.winfo_pointerxy()
        
        popup = tk.Toplevel(self.root)
        popup.title("Emojis")
        popup.geometry(f"300x150+{pos[0]}+{pos[1]}")
        popup.configure(bg='#1f1f1f')
        
        frame = tk.Frame(popup, bg='#1f1f1f')
        frame.pack(padx=10, pady=10)
        
        row = 0
        col = 0
        for emoji in emojis:
            btn = tk.Button(frame, text=emoji, bg='#2f2f2f', fg='white',
                           font=('Arial', 16), width=2, height=1,
                           command=lambda e=emoji: self.insert_emoji(e))
            btn.grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 5:
                col = 0
                row += 1
    
    def insert_emoji(self, emoji):
        """Insert emoji into message"""
        self.message_entry.insert('insert', emoji)
    
    def show_chat_menu(self, chat):
        """Show chat menu"""
        menu = tk.Menu(self.root, tearoff=0, bg='#1f1f1f', fg='white')
        menu.add_command(label="📌 Pin", command=lambda: self.pin_chat(chat))
        menu.add_command(label="🔕 Mute", command=lambda: self.mute_chat(chat))
        menu.add_command(label="📁 Archive", command=lambda: self.archive_chat(chat))
        menu.add_separator()
        menu.add_command(label="🗑️ Delete", command=lambda: self.delete_chat(chat))
        
        pos = self.root.winfo_pointerxy()
        menu.post(pos[0], pos[1])
    
    def pin_chat(self, chat):
        """Pin a chat"""
        for c in self.chats:
            if c.get('id') == chat.get('id'):
                c['pinned'] = not c.get('pinned', False)
                break
        self.save_chats()
        self.refresh_chat_list()
    
    def mute_chat(self, chat):
        """Mute a chat"""
        for c in self.chats:
            if c.get('id') == chat.get('id'):
                c['muted'] = not c.get('muted', False)
                break
        self.save_chats()
    
    def archive_chat(self, chat):
        """Archive a chat"""
        for i, c in enumerate(self.chats):
            if c.get('id') == chat.get('id'):
                self.archived_chats.append(c)
                del self.chats[i]
                break
        self.save_chats()
        self.refresh_chat_list()
    
    def delete_chat(self, chat):
        """Delete a chat"""
        if messagebox.askyesno("Delete Chat", f"Delete chat with {chat['name']}?"):
            for i, c in enumerate(self.chats):
                if c.get('id') == chat.get('id'):
                    del self.chats[i]
                    break
            
            if chat.get('id') in self.messages:
                del self.messages[chat.get('id')]
            
            self.save_chats()
            self.save_messages()
            self.refresh_chat_list()
            self.show_empty_chat()
    
    def show_archived(self):
        """Show archived chats"""
        # Create archive window
        archive_win = tk.Toplevel(self.root)
        archive_win.title("Archived Chats")
        archive_win.geometry("350x500")
        archive_win.configure(bg='#1f1f1f')
        
        tk.Label(archive_win, text="📁 Archived Chats", bg='#1f1f1f', fg='white',
                font=('Arial', 16, 'bold')).pack(pady=10)
        
        if not self.archived_chats:
            tk.Label(archive_win, text="No archived chats", bg='#1f1f1f', fg='#888',
                    font=('Arial', 12)).pack(pady=20)
        else:
            frame = tk.Frame(archive_win, bg='#1f1f1f')
            frame.pack(fill='both', expand=True, padx=10)
            
            for chat in self.archived_chats:
                chat_frame = tk.Frame(frame, bg='#1f1f1f')
                chat_frame.pack(fill='x', pady=2)
                
                tk.Label(chat_frame, text=f"{chat['avatar']} {chat['name']}",
                        bg='#1f1f1f', fg='white', font=('Arial', 12)).pack(side='left')
                
                tk.Button(chat_frame, text="Unarchive", bg='#2f2f2f', fg='white',
                         font=('Arial', 10), command=lambda c=chat: self.unarchive_chat(c, archive_win)
                        ).pack(side='right')
    
    def unarchive_chat(self, chat, window):
        """Unarchive a chat"""
        for i, c in enumerate(self.archived_chats):
            if c.get('id') == chat.get('id'):
                self.chats.append(c)
                del self.archived_chats[i]
                break
        self.save_chats()
        window.destroy()
        self.refresh_chat_list()
    
    def show_chats(self):
        """Show chats tab"""
        self.chats_tab.config(bg='#2f2f2f', fg='white')
        self.contacts_tab.config(bg='#1f1f1f', fg='#888')
        self.refresh_chat_list()
    
    def show_contacts(self):
        """Show contacts tab"""
        self.chats_tab.config(bg='#1f1f1f', fg='#888')
        self.contacts_tab.config(bg='#2f2f2f', fg='white')
        
        # Clear and show contacts
        for widget in self.chat_scrollable.winfo_children():
            widget.destroy()
        
        # Create a special Saved Messages entry at the top
        saved_frame = tk.Frame(self.chat_scrollable, bg='#1f1f1f', height=60)
        saved_frame.pack(fill='x', pady=1)
        saved_frame.pack_propagate(False)
        
        # Store a special identifier
        saved_frame.is_saved = True
        
        saved_avatar = tk.Frame(saved_frame, bg='#fbc02d', width=50, height=50)
        saved_avatar.pack(side='left', padx=(15,10), pady=10)
        saved_avatar.pack_propagate(False)
        
        tk.Label(saved_avatar, text="📌", bg='#fbc02d', fg='white',
                font=('Arial', 20)).pack(expand=True)
        
        saved_info = tk.Frame(saved_frame, bg='#1f1f1f')
        saved_info.pack(side='left', fill='both', expand=True, pady=10)
        
        tk.Label(saved_info, text="Saved Messages", bg='#1f1f1f', fg='white',
                font=('Arial', 12, 'bold')).pack(anchor='w')
        
        tk.Label(saved_info, text="Your cloud storage", bg='#1f1f1f', fg='#888',
                font=('Arial', 10)).pack(anchor='w')
        
        # Message button for Saved Messages
        saved_btn = tk.Button(saved_frame, text="💬", bg='#2f2f2f', fg='white',
                             font=('Arial', 12), 
                             command=lambda: self.open_saved_messages())
        saved_btn.pack(side='right', padx=10, pady=15)
        
        # Make the whole frame clickable
        saved_frame.bind('<Button-1>', lambda e: self.open_saved_messages())
        saved_avatar.bind('<Button-1>', lambda e: self.open_saved_messages())
        saved_info.bind('<Button-1>', lambda e: self.open_saved_messages())
        
        # Add New Contact button
        new_contact_btn = tk.Button(self.chat_scrollable, text="+ Add New Contact", 
                                   bg='#2f2f2f', fg='white', font=('Arial', 12),
                                   padx=10, pady=8, command=self.add_new_contact)
        new_contact_btn.pack(fill='x', padx=10, pady=5)
        
        # Separator
        sep = tk.Frame(self.chat_scrollable, bg='#2f2f2f', height=1)
        sep.pack(fill='x', pady=5)
        
        if not self.contacts:
            empty = tk.Label(self.chat_scrollable, text="No contacts yet", bg='#1f1f1f', fg='#888',
                            font=('Arial', 12))
            empty.pack(pady=20)
        else:
            for contact in self.contacts:
                frame = tk.Frame(self.chat_scrollable, bg='#1f1f1f', height=60)
                frame.pack(fill='x', pady=1)
                frame.pack_propagate(False)
                
                # Store contact info
                frame.contact = contact
                
                # Avatar
                avatar = tk.Frame(frame, bg=contact.get('color', '#4a6da8'), width=40, height=40)
                avatar.pack(side='left', padx=(15, 10), pady=10)
                avatar.pack_propagate(False)
                
                tk.Label(avatar, text=contact.get('avatar', '👤'), bg=contact.get('color', '#4a6da8'),
                        fg='white', font=('Arial', 16)).pack(expand=True)
                
                # Info
                info = tk.Frame(frame, bg='#1f1f1f')
                info.pack(side='left', fill='both', expand=True, pady=10)
                
                name = tk.Label(info, text=contact['name'], bg='#1f1f1f', fg='white',
                               font=('Arial', 12, 'bold'))
                name.pack(anchor='w')
                
                username = tk.Label(info, text=f"@{contact['username']}", bg='#1f1f1f', fg='#888',
                                   font=('Arial', 10))
                username.pack(anchor='w')
                
                # Message button
                msg_btn = tk.Button(frame, text="💬", bg='#2f2f2f', fg='white',
                                   font=('Arial', 12), 
                                   command=lambda c=contact: self.message_contact(c))
                msg_btn.pack(side='right', padx=10, pady=15)
                
                # Make frame clickable
                frame.bind('<Button-1>', lambda e, c=contact: self.message_contact(c))
                avatar.bind('<Button-1>', lambda e, c=contact: self.message_contact(c))
                info.bind('<Button-1>', lambda e, c=contact: self.message_contact(c))
    
    def add_new_contact(self):
        """Add a new contact"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Contact")
        dialog.geometry("350x300")
        dialog.configure(bg='#1f1f1f')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Form
        form = tk.Frame(dialog, bg='#1f1f1f', padx=20, pady=20)
        form.pack(fill='both', expand=True)
        
        tk.Label(form, text="Add New Contact", bg='#1f1f1f', fg='white',
                font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        tk.Label(form, text="Name:", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        name_entry = tk.Entry(form, bg='#2f2f2f', fg='white',
                             insertbackground='white', font=('Arial', 12),
                             width=30, bd=0, highlightthickness=1,
                             highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        name_entry.pack(pady=(0, 10))
        name_entry.focus_set()
        
        tk.Label(form, text="Username:", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        username_entry = tk.Entry(form, bg='#2f2f2f', fg='white',
                                 insertbackground='white', font=('Arial', 12),
                                 width=30, bd=0, highlightthickness=1,
                                 highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        username_entry.pack(pady=(0, 10))
        
        tk.Label(form, text="Phone (optional):", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        phone_entry = tk.Entry(form, bg='#2f2f2f', fg='white',
                              insertbackground='white', font=('Arial', 12),
                              width=30, bd=0, highlightthickness=1,
                              highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        phone_entry.pack(pady=(0, 20))
        
        def save_contact():
            name = name_entry.get().strip()
            username = username_entry.get().strip()
            phone = phone_entry.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter a name")
                return
            
            if not username:
                # Generate username from name
                username = name.lower().replace(' ', '_') + str(random.randint(100, 999))
            
            # Create contact
            contact = {
                'id': f"contact_{int(time.time())}_{random.randint(1000, 9999)}",
                'name': name,
                'username': username,
                'phone': phone,
                'avatar': self.get_random_avatar(),
                'color': self.get_random_color()
            }
            
            self.contacts.append(contact)
            self.save_contacts()
            self.show_contacts()  # Refresh contacts view
            dialog.destroy()
            
            messagebox.showinfo("Success", f"Contact {name} added successfully!")
        
        # Buttons
        btn_frame = tk.Frame(form, bg='#1f1f1f')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(btn_frame, text="Cancel", bg='#2f2f2f', fg='white',
                 font=('Arial', 11), padx=20, command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Save", bg=self.theme_color, fg='white',
                 font=('Arial', 11), padx=20, command=save_contact).pack(side='right', padx=5)
    
    def message_contact(self, contact):
        """Start chat with contact"""
        # Check if it's the saved messages (special case)
        if isinstance(contact, dict) and contact.get('name') == 'Saved Messages':
            self.open_saved_messages()
            return
        
        # Check if chat exists
        for chat in self.chats:
            if isinstance(contact, dict) and chat.get('id') == contact.get('id'):
                self.open_chat(chat)
                return
        
        # Create new chat
        if isinstance(contact, dict):
            new_chat = {
                'id': contact.get('id', f"contact_{int(time.time())}"),
                'name': contact['name'],
                'last_message': 'Start messaging',
                'time': 'now',
                'avatar': contact.get('avatar', '👤'),
                'color': contact.get('color', self.get_random_color())
            }
            self.chats.append(new_chat)
            self.save_chats()
            self.refresh_chat_list()
            self.show_chats()
            self.open_chat(new_chat)
    
    def get_random_avatar(self):
        """Get random avatar"""
        avatars = ['👤', '👥', '👨', '👩', '👶', '🧑', '🐱', '🐶', '🐼', '🦊']
        return random.choice(avatars)
    
    def get_random_color(self):
        """Get random color"""
        colors = ['#2b5278', '#8e6b3c', '#4a6da8', '#2e7d32', '#c44536', '#7b1fa2', '#00897b', '#f57c00']
        return random.choice(colors)
    
    # ==================== MENU ====================
    
    def toggle_menu(self):
        """Toggle menu sidebar"""
        if self.menu_visible:
            self.close_menu()
        else:
            self.show_menu()
    
    def show_menu(self):
        """Show menu"""
        self.menu_visible = True
        
        self.menu_window = tk.Toplevel(self.root)
        self.menu_window.title("")
        self.menu_window.geometry("250x600")
        self.menu_window.configure(bg='#1f1f1f')
        self.menu_window.overrideredirect(True)
        
        x = self.root.winfo_x() + 10
        y = self.root.winfo_y() + 70
        self.menu_window.geometry(f"+{x}+{y}")
        
        frame = tk.Frame(self.menu_window, bg='#1f1f1f')
        frame.pack(fill='both', expand=True)
        
        # User info
        user = tk.Frame(frame, bg='#2f2f2f', height=80)
        user.pack(fill='x')
        user.pack_propagate(False)
        
        avatar = tk.Frame(user, bg=self.theme_color, width=50, height=50)
        avatar.pack(side='left', padx=15, pady=15)
        avatar.pack_propagate(False)
        
        first = self.display_name[0].upper() if self.display_name else "👤"
        tk.Label(avatar, text=first, bg=self.theme_color, fg='white',
                font=('Arial', 20)).pack(expand=True)
        
        name_frame = tk.Frame(user, bg='#2f2f2f')
        name_frame.pack(side='left', fill='both', expand=True, pady=15)
        
        tk.Label(name_frame, text=self.display_name, bg='#2f2f2f', fg='white',
                font=('Arial', 14, 'bold')).pack(anchor='w')
        
        tk.Button(name_frame, text="Set Emoji Status", bg='#2f2f2f', fg='#888',
                 font=('Arial', 10), bd=0, anchor='w').pack(anchor='w')
        
        # Separator
        sep1 = tk.Frame(frame, bg='#2f2f2f', height=1)
        sep1.pack(fill='x', pady=5)
        
        # Menu items
        items = [
            ("New Contact", "👤➕", self.add_new_contact),
            ("New Group", "👥", self.new_group),
            ("New Channel", "📢", self.new_channel),
            ("Contacts", "📇", self.show_contacts_tab),
            ("Calls", "📞", self.open_calls),
            ("Saved Messages", "📌", self.open_saved_messages),
            ("Settings", "⚙️", self.open_settings),
            ("Night Mode", "🌙", self.toggle_night_mode)
        ]
        
        for text, icon, cmd in items:
            btn = tk.Button(frame, text=f"  {icon}  {text}", bg='#1f1f1f', fg='white',
                          font=('Arial', 12), bd=0, anchor='w', padx=20, pady=10,
                          activebackground='#2f2f2f', command=cmd)
            btn.pack(fill='x')
        
        # Separator
        sep2 = tk.Frame(frame, bg='#2f2f2f', height=1)
        sep2.pack(fill='x', pady=5)
        
        # My Profile at bottom
        profile_btn = tk.Button(frame, text="  👤  My Profile", bg='#1f1f1f', fg='white',
                               font=('Arial', 12), bd=0, anchor='w', padx=20, pady=10,
                               activebackground='#2f2f2f', command=self.open_profile)
        profile_btn.pack(fill='x', side='bottom')
        
        self.menu_window.bind('<FocusOut>', lambda e: self.close_menu())
    
    def close_menu(self):
        """Close menu"""
        self.menu_visible = False
        if self.menu_window:
            self.menu_window.destroy()
    
    # ==================== MENU ACTIONS ====================
    
    def open_profile(self):
        """Open profile window"""
        self.close_menu()
        
        profile = tk.Toplevel(self.root)
        profile.title("Profile")
        profile.geometry("350x500")
        profile.configure(bg='#0f0f0f')
        
        # Content
        main = tk.Frame(profile, bg='#1f1f1f', padx=30, pady=30)
        main.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Avatar
        avatar_frame = tk.Frame(main, bg=self.theme_color, width=100, height=100)
        avatar_frame.pack(pady=(0, 20))
        avatar_frame.pack_propagate(False)
        
        first = self.display_name[0].upper() if self.display_name else "👤"
        tk.Label(avatar_frame, text=first, bg=self.theme_color, fg='white',
                font=('Arial', 40)).pack(expand=True)
        
        tk.Button(main, text="Change Photo", bg='#2f2f2f', fg='white',
                 font=('Arial', 11), command=self.change_photo).pack(pady=5)
        
        # Info
        info_frame = tk.Frame(main, bg='#1f1f1f')
        info_frame.pack(fill='x', pady=10)
        
        tk.Label(info_frame, text="Name", bg='#1f1f1f', fg='#888',
                font=('Arial', 10)).pack(anchor='w')
        tk.Label(info_frame, text=self.display_name, bg='#1f1f1f', fg='white',
                font=('Arial', 14)).pack(anchor='w', pady=(0, 10))
        
        tk.Label(info_frame, text="Username", bg='#1f1f1f', fg='#888',
                font=('Arial', 10)).pack(anchor='w')
        tk.Label(info_frame, text=f"@{self.username}", bg='#1f1f1f', fg='white',
                font=('Arial', 14)).pack(anchor='w', pady=(0, 10))
        
        tk.Label(info_frame, text="Phone", bg='#1f1f1f', fg='#888',
                font=('Arial', 10)).pack(anchor='w')
        tk.Label(info_frame, text=self.phone or "Not set", bg='#1f1f1f', fg='white',
                font=('Arial', 14)).pack(anchor='w', pady=(0, 10))
        
        tk.Label(info_frame, text="Bio", bg='#1f1f1f', fg='#888',
                font=('Arial', 10)).pack(anchor='w')
        
        bio_entry = tk.Text(info_frame, bg='#2f2f2f', fg='white',
                           font=('Arial', 11), height=4, width=30)
        bio_entry.pack(anchor='w', pady=(0, 10))
        bio_entry.insert('1.0', self.bio)
        
        def save_bio():
            self.bio = bio_entry.get('1.0', 'end-1c').strip()
            self.save_user_data()
            messagebox.showinfo("Success", "Bio updated")
        
        tk.Button(info_frame, text="Save Bio", bg=self.theme_color, fg='white',
                 font=('Arial', 11), command=save_bio).pack()
    
    def change_photo(self):
        """Change profile photo"""
        filename = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if filename:
            dest = os.path.join(self.data_dir, "profile_photo.png")
            shutil.copy2(filename, dest)
            self.profile_photo = dest
            messagebox.showinfo("Success", "Profile photo updated")
    
    def new_group(self):
        """Create new group"""
        self.close_menu()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("New Group")
        dialog.geometry("350x300")
        dialog.configure(bg='#1f1f1f')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Form
        form = tk.Frame(dialog, bg='#1f1f1f', padx=20, pady=20)
        form.pack(fill='both', expand=True)
        
        tk.Label(form, text="Create New Group", bg='#1f1f1f', fg='white',
                font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        tk.Label(form, text="Group Name:", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        name_entry = tk.Entry(form, bg='#2f2f2f', fg='white',
                             insertbackground='white', font=('Arial', 12),
                             width=30, bd=0, highlightthickness=1,
                             highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        name_entry.pack(pady=(0, 15))
        name_entry.focus_set()
        
        tk.Label(form, text="Select Members (from contacts):", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        # Contact selection listbox
        list_frame = tk.Frame(form, bg='#2f2f2f')
        list_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        contacts_list = tk.Listbox(list_frame, bg='#2f2f2f', fg='white',
                                   selectmode='multiple', yscrollcommand=scrollbar.set,
                                   font=('Arial', 11), height=5)
        contacts_list.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=contacts_list.yview)
        
        # Populate contacts
        if self.contacts:
            for contact in self.contacts:
                contacts_list.insert(tk.END, f"{contact['name']} (@{contact['username']})")
        else:
            contacts_list.insert(tk.END, "No contacts available")
            contacts_list.config(state='disabled')
        
        def create_group():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a group name")
                return
            
            # Get selected contacts
            selected_indices = contacts_list.curselection()
            selected_contacts = []
            for idx in selected_indices:
                if idx < len(self.contacts):
                    selected_contacts.append(self.contacts[idx])
            
            # Create group chat
            chat_id = f"group_{int(time.time())}"
            group_chat = {
                'id': chat_id,
                'name': name,
                'last_message': 'Group created',
                'time': 'now',
                'avatar': '👥',
                'color': self.get_random_color(),
                'is_group': True,
                'members': [self.user_id] + [c.get('id') for c in selected_contacts],
                'member_names': [self.display_name] + [c['name'] for c in selected_contacts]
            }
            
            self.chats.append(group_chat)
            self.save_chats()
            self.refresh_chat_list()
            self.show_chats()
            
            # Add welcome message
            if chat_id not in self.messages:
                self.messages[chat_id] = []
            
            welcome_msg = {
                'text': f"Group '{name}' created with {len(selected_contacts)} members",
                'sent': True,
                'time': time.time(),
                'sender': self.display_name,
                'system': True
            }
            self.messages[chat_id].append(welcome_msg)
            self.save_messages()
            
            dialog.destroy()
            messagebox.showinfo("Success", f"Group '{name}' created successfully!")
            self.open_chat(group_chat)
        
        # Buttons
        btn_frame = tk.Frame(form, bg='#1f1f1f')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(btn_frame, text="Cancel", bg='#2f2f2f', fg='white',
                 font=('Arial', 11), padx=20, command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Create", bg=self.theme_color, fg='white',
                 font=('Arial', 11), padx=20, command=create_group).pack(side='right', padx=5)
    
    def new_channel(self):
        """Create new channel"""
        self.close_menu()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("New Channel")
        dialog.geometry("350x250")
        dialog.configure(bg='#1f1f1f')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Form
        form = tk.Frame(dialog, bg='#1f1f1f', padx=20, pady=20)
        form.pack(fill='both', expand=True)
        
        tk.Label(form, text="Create New Channel", bg='#1f1f1f', fg='white',
                font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        tk.Label(form, text="Channel Name:", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        name_entry = tk.Entry(form, bg='#2f2f2f', fg='white',
                             insertbackground='white', font=('Arial', 12),
                             width=30, bd=0, highlightthickness=1,
                             highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        name_entry.pack(pady=(0, 15))
        name_entry.focus_set()
        
        tk.Label(form, text="Description (optional):", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        
        desc_entry = tk.Entry(form, bg='#2f2f2f', fg='white',
                             insertbackground='white', font=('Arial', 12),
                             width=30, bd=0, highlightthickness=1,
                             highlightcolor=self.theme_color, highlightbackground='#3f3f3f')
        desc_entry.pack(pady=(0, 20))
        
        def create_channel():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a channel name")
                return
            
            description = desc_entry.get().strip()
            
            # Create channel chat
            chat_id = f"channel_{int(time.time())}"
            channel_chat = {
                'id': chat_id,
                'name': name,
                'last_message': 'Channel created',
                'time': 'now',
                'avatar': '📢',
                'color': self.get_random_color(),
                'is_channel': True,
                'description': description,
                'subscribers': [self.user_id]
            }
            
            self.chats.append(channel_chat)
            self.save_chats()
            self.refresh_chat_list()
            self.show_chats()
            
            # Add welcome message
            if chat_id not in self.messages:
                self.messages[chat_id] = []
            
            welcome_msg = {
                'text': f"Channel '{name}' created. This is your channel. Share it with others!",
                'sent': True,
                'time': time.time(),
                'sender': self.display_name,
                'system': True
            }
            self.messages[chat_id].append(welcome_msg)
            self.save_messages()
            
            dialog.destroy()
            messagebox.showinfo("Success", f"Channel '{name}' created successfully!")
            self.open_chat(channel_chat)
        
        # Buttons
        btn_frame = tk.Frame(form, bg='#1f1f1f')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(btn_frame, text="Cancel", bg='#2f2f2f', fg='white',
                 font=('Arial', 11), padx=20, command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Create", bg=self.theme_color, fg='white',
                 font=('Arial', 11), padx=20, command=create_channel).pack(side='right', padx=5)
    
    def show_contacts_tab(self):
        """Show contacts tab"""
        self.close_menu()
        self.show_contacts()
    
    def open_calls(self):
        """Open calls"""
        self.close_menu()
        
        calls = tk.Toplevel(self.root)
        calls.title("Calls")
        calls.geometry("350x400")
        calls.configure(bg='#1f1f1f')
        
        tk.Label(calls, text="Recent Calls", bg='#1f1f1f', fg='white',
                font=('Arial', 16, 'bold')).pack(pady=10)
        
        # Sample calls
        calls_list = [
            ("Mom", "📞", "#4a6da8", "Today, 10:30"),
            ("Alex", "👤", "#2e7d32", "Yesterday, 18:45"),
            ("Work Group", "👥", "#c44536", "2 days ago"),
        ]
        
        for name, icon, color, time in calls_list:
            frame = tk.Frame(calls, bg='#1f1f1f')
            frame.pack(fill='x', padx=10, pady=2)
            
            avatar = tk.Frame(frame, bg=color, width=40, height=40)
            avatar.pack(side='left', padx=5, pady=5)
            avatar.pack_propagate(False)
            tk.Label(avatar, text=icon, bg=color, fg='white',
                    font=('Arial', 16)).pack(expand=True)
            
            tk.Label(frame, text=name, bg='#1f1f1f', fg='white',
                    font=('Arial', 12)).pack(side='left', padx=10)
            
            tk.Label(frame, text=time, bg='#1f1f1f', fg='#888',
                    font=('Arial', 10)).pack(side='right', padx=10)
    
    def open_saved_messages(self):
        """Open saved messages"""
        self.close_menu()
        
        # Find saved messages chat
        saved_chat = None
        for chat in self.chats:
            if chat.get('id') == 'saved':
                saved_chat = chat
                break
        
        if not saved_chat:
            # Create saved messages if it doesn't exist
            saved_chat = {
                'id': 'saved',
                'name': 'Saved Messages',
                'last_message': 'Your notes and media',
                'time': 'now',
                'avatar': '📌',
                'color': '#fbc02d',
                'pinned': True
            }
            self.chats.insert(0, saved_chat)  # Insert at beginning
            self.save_chats()
            self.refresh_chat_list()
        
        self.open_chat(saved_chat)
    
    def open_settings(self):
        """Open settings window"""
        self.close_menu()
        
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("500x600")
        settings.configure(bg='#0f0f0f')
        
        # Header
        header = tk.Frame(settings, bg='#1f1f1f', height=50)
        header.pack(fill='x')
        tk.Label(header, text="Settings", bg='#1f1f1f', fg='white',
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Content
        canvas = tk.Canvas(settings, bg='#0f0f0f', highlightthickness=0)
        scroll = tk.Scrollbar(settings, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg='#0f0f0f')
        
        scrollable.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scroll.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        
        # Profile preview
        profile = tk.Frame(scrollable, bg='#1f1f1f')
        profile.pack(fill='x', padx=10, pady=10)
        
        tk.Label(profile, text="Profile", bg='#1f1f1f', fg='white',
                font=('Arial', 12, 'bold')).pack(anchor='w', padx=15, pady=(10, 5))
        
        prof_row = tk.Frame(profile, bg='#1f1f1f')
        prof_row.pack(fill='x', padx=15, pady=10)
        
        avatar = tk.Frame(prof_row, bg=self.theme_color, width=50, height=50)
        avatar.pack(side='left')
        avatar.pack_propagate(False)
        tk.Label(avatar, text=self.display_name[0].upper(), bg=self.theme_color,
                fg='white', font=('Arial', 20)).pack(expand=True)
        
        info = tk.Frame(prof_row, bg='#1f1f1f', padx=10)
        info.pack(side='left', fill='both', expand=True)
        tk.Label(info, text=self.display_name, bg='#1f1f1f', fg='white',
                font=('Arial', 14)).pack(anchor='w')
        tk.Label(info, text=f"@{self.username}", bg='#1f1f1f', fg='#888',
                font=('Arial', 11)).pack(anchor='w')
        
        # Settings sections
        sections = [
            ("Notifications", "🔔", "notifications"),
            ("Privacy", "🔒", None),
            ("Data", "📊", None),
            ("Chat Settings", "💬", None),
            ("Theme", "🎨", "theme"),
            ("Language", "🌐", None),
            ("Storage", "💾", None)
        ]
        
        for label, icon, var in sections:
            section = tk.Frame(scrollable, bg='#1f1f1f')
            section.pack(fill='x', padx=10, pady=2)
            
            row = tk.Frame(section, bg='#1f1f1f')
            row.pack(fill='x', padx=15, pady=12)
            
            tk.Label(row, text=f"{icon}  {label}", bg='#1f1f1f', fg='white',
                    font=('Arial', 12)).pack(side='left')
            
            if var == 'notifications':
                var = tk.BooleanVar(value=self.notifications)
                cb = tk.Checkbutton(row, bg='#1f1f1f', variable=var,
                                   command=lambda: self.toggle_notifications(var))
                cb.pack(side='right')
            elif var == 'theme':
                colors = ['#4a6da8', '#c44536', '#2e7d32', '#8e6b3c', '#7b1fa2']
                color_frame = tk.Frame(row, bg='#1f1f1f')
                color_frame.pack(side='right')
                
                for color in colors:
                    btn = tk.Button(color_frame, bg=color, width=2, height=1,
                                   command=lambda c=color: self.change_theme(c))
                    btn.pack(side='left', padx=2)
    
    def toggle_notifications(self, var):
        """Toggle notifications"""
        self.notifications = var.get()
        self.save_user_data()
    
    def change_theme(self, color):
        """Change theme color"""
        self.theme_color = color
        self.save_user_data()
        messagebox.showinfo("Theme", "Theme changed. Restart to see changes.")
    
    def toggle_night_mode(self):
        """Toggle night mode"""
        self.close_menu()
        self.night_mode = not self.night_mode
        if self.night_mode:
            self.root.configure(bg='#0f0f0f')
            messagebox.showinfo("Night Mode", "Dark mode activated")
        else:
            self.root.configure(bg='#ffffff')
            messagebox.showinfo("Night Mode", "Light mode activated")
    
    # ==================== UTILITIES ====================
    
    def clear_search_placeholder(self, e):
        if self.search_entry.get() == "Search":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg='white')
    
    def restore_search_placeholder(self, e):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search")
            self.search_entry.config(fg='#888')
    
    def search_chats(self, e):
        term = self.search_entry.get().lower()
        if term == "search":
            return
        
        for widget in self.chat_scrollable.winfo_children():
            if hasattr(widget, 'chat_id'):
                chat = next((c for c in self.chats if c.get('id') == widget.chat_id), None)
                if chat and (term in chat['name'].lower() or term in chat['last_message'].lower()):
                    widget.pack(fill='x', pady=1)
                else:
                    widget.pack_forget()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TelegramStyleMessenger()
    app.run()

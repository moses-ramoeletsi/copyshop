import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

class LoginUI:
    def __init__(self, root, auth_manager, on_login_success):
        self.root = root
        self.auth_manager = auth_manager
        self.on_login_success = on_login_success
        self.login_window = tk.Toplevel(root)
        self.login_window.title("Print Shop Login")
        self.center_window(460, 580)
        self.login_window.configure(bg="#ffffff")
        self.login_window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.create_login_ui()

    def center_window(self, width, height):
        """Center the login window on the screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.login_window.geometry(f"{width}x{height}+{x}+{y}")

    def create_login_ui(self):
        """Create modern login form."""
        container = tk.Frame(self.login_window, bg="#ffffff", padx=30, pady=30)
        container.pack(fill="both", expand=True)
        
        logo_frame = tk.Frame(container, bg="#ffffff")
        logo_frame.pack(pady=(10, 30))
        
        logo_label = tk.Label(
            logo_frame,
            text="AlphaPrinting",
            font=('Helvetica', 32, 'bold'),
            foreground='#1e40af',
            bg="#ffffff"
        )
        logo_label.pack()
        
        tk.Label(
            logo_frame,
            text="Welcome back",
            font=('Helvetica', 14),
            fg="#666666",
            bg="#ffffff"
        ).pack(pady=(5, 0))

        form_frame = tk.Frame(container, bg="#ffffff")
        form_frame.pack(fill="x", pady=20)

        username_frame = tk.Frame(form_frame, bg="#ffffff")
        username_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            username_frame,
            text="Username",
            font=("Helvetica", 12),
            fg="#333333",
            bg="#ffffff"
        ).pack(anchor="w")
        
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(
            username_frame,
            textvariable=self.username_var,
            font=("Helvetica", 12),
            bg="#f8f9fa",
            fg="#333333",
            insertbackground="#333333",
            relief="flat",
            width=30
        )
        username_entry.pack(fill="x", pady=(5, 0), ipady=8)
        
        password_frame = tk.Frame(form_frame, bg="#ffffff")
        password_frame.pack(fill="x", pady=(0, 25))
        
        tk.Label(
            password_frame,
            text="Password",
            font=("Helvetica", 12),
            fg="#333333",
            bg="#ffffff"
        ).pack(anchor="w")
        
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(
            password_frame,
            textvariable=self.password_var,
            show="•",
            font=("Helvetica", 12),
            bg="#f8f9fa",
            fg="#333333",
            insertbackground="#333333",
            relief="flat",
            width=30
        )
        password_entry.pack(fill="x", pady=(5, 0), ipady=8)

        self.login_button = tk.Button(
            container,
            text="Log In",
            command=self.login,
            font=("Helvetica", 14, "bold"),
            bg="#1e40af",
            fg="white",
            activebackground="#1e3a8a",
            activeforeground="white",
            relief="flat",
            cursor="hand2"
        )
        self.login_button.pack(fill="x", pady=(20, 10), ipady=10)
        
        self.login_button.bind("<Enter>", self.on_button_hover)
        self.login_button.bind("<Leave>", self.on_button_leave)

    def on_button_hover(self, event):
        """Handle button hover effect."""
        self.login_button.configure(bg="#1e3a8a")

    def on_button_leave(self, event):
        """Handle button hover leave effect."""
        self.login_button.configure(bg="#1e40af")

    def login(self):
        """Handle login attempt."""
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        if self.auth_manager.authenticate(username, password):
            self.login_window.destroy()
            self.on_login_success()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def on_close(self):
        """Handle window close button click."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.quit()
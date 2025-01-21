import tkinter as tk
from tkinter import ttk, messagebox

class UserManagementUI:
    def __init__(self, parent, auth_manager):
        self.dialog = tk.Toplevel(parent)
        self.auth_manager = auth_manager
        self.dialog.title("User Management")
        self.dialog.geometry("800x500")  # Made window larger
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_ui()

    def create_ui(self):
        """Create user management interface"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # User list
        list_frame = ttk.LabelFrame(main_frame, text="Users", padding="10")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add scrollbar
        tree_scroll = ttk.Scrollbar(list_frame)
        tree_scroll.pack(side='right', fill='y')
        
        columns = ('Username', 'Role', 'Full Name', 'Created At', 'Created By')
        self.user_tree = ttk.Treeview(list_frame, columns=columns, show='headings',
                                     yscrollcommand=tree_scroll.set)
        
        # Configure scrollbar
        tree_scroll.config(command=self.user_tree.yview)
        
        # Configure columns
        for col in columns:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=150)  # Made columns wider
        
        self.user_tree.pack(fill='both', expand=True)
        
        # New user form
        form_frame = ttk.LabelFrame(main_frame, text="Add New User", padding="10")
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Create grid for form
        form_frame.columnconfigure(1, weight=1)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, pady=2, sticky='e', padx=5)
        self.username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.username_var).grid(row=0, column=1, pady=2, sticky='ew')
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, pady=2, sticky='e', padx=5)
        self.password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.password_var, show="*").grid(row=1, column=1, pady=2, sticky='ew')
        
        # Full Name
        ttk.Label(form_frame, text="Full Name:").grid(row=2, column=0, pady=2, sticky='e', padx=5)
        self.fullname_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.fullname_var).grid(row=2, column=1, pady=2, sticky='ew')
        
        # Role
        ttk.Label(form_frame, text="Role:").grid(row=3, column=0, pady=2, sticky='e', padx=5)
        self.role_var = tk.StringVar(value="user")
        ttk.Combobox(form_frame, textvariable=self.role_var,
                    values=["user", "admin"],
                    state="readonly").grid(row=3, column=1, pady=2, sticky='ew')
        
        # Add User button
        ttk.Button(form_frame, text="Add User",
                  command=self.add_user).grid(row=4, column=0, columnspan=2, pady=10)
        
        self.update_user_list()

    def add_user(self):
        """Add new user"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        full_name = self.fullname_var.get().strip()
        role = self.role_var.get()
        
        if not all([username, password, full_name]):
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return
        
        if self.auth_manager.register_user(
            username=username,
            password=password,
            role=role,
            full_name=full_name,
            created_by=self.auth_manager.current_user.username
        ):
            messagebox.showinfo("Success", "User added successfully")
            self.update_user_list()
            # Clear form
            for var in [self.username_var, self.password_var, self.fullname_var]:
                var.set("")
        else:
            messagebox.showerror("Error", "Username already exists")

    def update_user_list(self):
        """Update user list display"""
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        for user in self.auth_manager.get_all_users():
            self.user_tree.insert('', 'end', values=user)
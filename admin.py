from calendar import calendar
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from tkcalendar import DateEntry 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AdminDashboardUI:
    def __init__(self, root, auth_manager, service):
        self.root = root
        self.auth_manager = auth_manager
        self.service = service
        
        
        self.root.title("Print Shop Admin Dashboard")
        self.root.state('zoomed')
        
        self.style = ttk.Style()
        self.current_theme = tk.StringVar(value="light")
        self.create_dashboard()

    def create_dashboard(self):
        """Create the main admin dashboard interface"""
     
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill='both', expand=True)
        
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(
            header_frame, 
            text=f"Welcome, {self.auth_manager.current_user.full_name}", 
            font=('Leelawadee', 16, 'bold')
        ).pack(side='left')
        
        theme_frame = ttk.Frame(header_frame)
        theme_frame.pack(side='right', padx=10)
        ttk.Label(theme_frame, text="Theme:").pack(side='left', padx=5)
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.current_theme,
            values=["light", "dark"],
            state="readonly",
            width=10
        )
        theme_combo.pack(side='left', padx=5)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        ttk.Button(
            header_frame, 
            text="Logout", 
            command=self.logout
        ).pack(side='right')

        notebook = ttk.Notebook(main_container)
        notebook.pack(fill='both', expand=True)

        dashboard_frame = ttk.Frame(notebook, padding="10")
        notebook.add(dashboard_frame, text="Dashboard")
        self.create_dashboard_overview(dashboard_frame)

        user_frame = ttk.Frame(notebook, padding="10")
        notebook.add(user_frame, text="User Management")
        self.create_user_management_tab(user_frame)

        stock_frame = ttk.Frame(notebook, padding="10")
        notebook.add(stock_frame, text="Stock")
        self.create_stock_tab(stock_frame)

        reports_frame = ttk.Frame(notebook, padding="10")
        notebook.add(reports_frame, text="Reports")
        self.create_reports_tab(reports_frame)

        settings_frame = ttk.Frame(notebook, padding="10")
        notebook.add(settings_frame, text="System Settings")
        self.create_settings_tab(settings_frame)

    def create_dashboard_overview(self, parent):
        """Create dashboard overview with real-time metrics from database"""
      
        metrics_frame = ttk.LabelFrame(parent, text="Key Metrics", padding="10")
        metrics_frame.pack(fill='x', pady=(0, 20))
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        active_users = len([user for user in self.auth_manager.get_all_users() if user[1] == "user"])
        
        self.service.db.cursor.execute('''
            SELECT COUNT(*), SUM(amount) 
            FROM transactions 
            WHERE date = ?
        ''', (today,))
        transactions_today, revenue_today = self.service.db.cursor.fetchone()
        transactions_today = transactions_today or 0
        revenue_today = revenue_today or 0
        
        low_stock_count = 0
        stock = self.service.inventory_model.get_stock()
        
        if 'paper' in stock and stock['paper']['total_sheets'] < self.service.stock_thresholds['paper']:
            low_stock_count += 1
        if 'file' in stock and stock['file']['quantity'] < self.service.stock_thresholds['file']:
            low_stock_count += 1
        if 'envelope' in stock and stock['envelope']['quantity'] < self.service.stock_thresholds['envelope']:
            low_stock_count += 1
        
        self.create_metric_card(metrics_frame, "Active Users", str(active_users), 0, 0)
        self.create_metric_card(metrics_frame, f"Today's Transactions", str(transactions_today), 0, 1)
        self.create_metric_card(metrics_frame, "Low Stock Items", str(low_stock_count), 0, 2)
        self.create_metric_card(metrics_frame, f"Today's Revenue", f"M{revenue_today:.2f}", 0, 3)
        
        charts_frame = ttk.Frame(parent)
        charts_frame.pack(fill='both', expand=True)
        
        self.create_activity_chart(charts_frame)
        self.create_stock_levels_chart(charts_frame)

    def create_activity_chart(self, parent):
        """Create activity chart with actual transaction data"""
        figure, ax = plt.subplots(figsize=(6, 4))
        
        dates = []
        activities = []
        
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            display_date = (datetime.now() - timedelta(days=i)).strftime('%a')
            dates.append(display_date)
            
            self.service.db.cursor.execute('''
                SELECT COUNT(*) 
                FROM transactions 
                WHERE date = ?
            ''', (date,))
            
            count = self.service.db.cursor.fetchone()[0]
            activities.append(count)
        
        ax.plot(dates, activities, marker='o')
        ax.set_title('Weekly Transaction Activity')
        ax.set_xlabel('Day')
        ax.set_ylabel('Number of Transactions')
        
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(figure, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_stock_levels_chart(self, parent):
        """Create stock levels chart with actual inventory data"""
        figure, ax = plt.subplots(figsize=(6, 4))
        
        stock = self.service.inventory_model.get_stock()
        categories = []
        quantities = []
        
        if 'paper' in stock:
            categories.append('Paper (sheets)')
            quantities.append(stock['paper']['total_sheets'])
        
        for item in ['file', 'envelope']:
            if item in stock:
                categories.append(item.capitalize())
                quantities.append(stock[item]['quantity'])
        
        bars = ax.bar(categories, quantities)
        ax.set_title('Current Stock Levels')
        ax.set_ylabel('Quantity')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(figure, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    def create_metric_card(self, parent, title, value, row, col):
        """Create a metric card widget"""
        card = ttk.Frame(parent, relief="solid", borderwidth=1)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(card, text=title, font=('Leelawadee', 10)).pack(pady=(5,0))
        ttk.Label(card, text=value, font=('Leelawadee', 14, 'bold')).pack(pady=(0,5))
        
        parent.grid_columnconfigure(col, weight=1)

    def create_user_management_tab(self, parent):
        """Create user management interface"""
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True)

        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(
            button_frame,
            text="Create New User",
            command=self.show_create_user_dialog
        ).pack(pady=(0, 10))

        ttk.Button(
            button_frame,
            text="Edit User",
            command=self.edit_selected_user
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame,
            text="Delete User",
            command=self.delete_selected_user
        ).pack(side='left', padx=5)


        columns = ('Username', 'Role', 'Full Name', 'Created At', 'Created By')
        self.users_table = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.users_table.heading(col, text=col)
            self.users_table.column(col, width=120)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.users_table.yview)
        self.users_table.configure(yscrollcommand=scrollbar.set)
        
        self.users_table.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.refresh_users_list()
    
    def edit_selected_user(self):
        """Edit the selected user"""
        selected_items = self.users_table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a user to edit")
            return
            
        user_data = self.users_table.item(selected_items[0])['values']
        username = user_data[0]
        
        if username == 'admin':
            messagebox.showwarning("Warning", "The default admin user cannot be edited")
            return
            
        self.show_edit_user_dialog(username)

    def show_edit_user_dialog(self, username):
        """Show dialog for editing a user"""
        all_users = self.auth_manager.get_all_users()
        user_data = None
        for user in all_users:
            if user[0] == username:
                user_data = user
                break
        
        if not user_data:
            messagebox.showerror("Error", "User not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit User")
        dialog.geometry("300x400")
        dialog.grab_set()  
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill='both', expand=True)

        fields = {
            'Username': tk.StringVar(value=user_data[0]),
            'Role': tk.StringVar(value=user_data[1]),
            'Full Name': tk.StringVar(value=user_data[2])
        }

        ttk.Label(frame, text="Username").pack()
        ttk.Entry(frame, textvariable=fields['Username'], state='disabled').pack()
        
        ttk.Label(frame, text="Role").pack()
        role_combo = ttk.Combobox(
            frame, 
            textvariable=fields['Role'], 
            values=['user', 'admin'],
            state='readonly'
        )
        role_combo.pack()
        
        ttk.Label(frame, text="Full Name").pack()
        ttk.Entry(frame, textvariable=fields['Full Name']).pack()

        ttk.Label(frame, text="New Password (leave blank to keep current)").pack()
        password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=password_var, show='*').pack()

        def save_changes():
            try:
                if not fields['Full Name'].get().strip():
                    messagebox.showerror("Error", "Full Name is required")
                    return
                    
                if self.auth_manager.update_user(
                    username=username,
                    new_password=password_var.get() if password_var.get() else None,
                    role=fields['Role'].get(),
                    full_name=fields['Full Name'].get()
                ):
                    messagebox.showinfo("Success", "User updated successfully")
                    self.refresh_users_list()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to update user")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        ttk.Button(
            frame,
            text="Save Changes",
            command=save_changes
        ).pack(pady=20)
       
    def delete_selected_user(self):
        """Delete the selected user"""
        selected_items = self.users_table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
            
        username = self.users_table.item(selected_items[0])['values'][0]
        
        if username == 'admin':
            messagebox.showwarning("Warning", "The default admin user cannot be deleted")
            return
            
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?"):
            if self.auth_manager.delete_user(username):
                messagebox.showinfo("Success", "User deleted successfully")
                self.refresh_users_list()
            else:
                messagebox.showerror("Error", "Failed to delete user")

    def create_reports_tab(self, parent):
        main_container = ttk.Frame(parent, padding="20")
        main_container.pack(fill='both', expand=True)
        
        date_frame = ttk.LabelFrame(main_container, text="Date Range", padding="15")
        date_frame.pack(fill='x', padx=10, pady=(0, 20))
        
        date_controls = ttk.Frame(date_frame)
        date_controls.pack(pady=10)
        
        from_frame = ttk.Frame(date_controls)
        from_frame.pack(side='left', padx=20)
        ttk.Label(from_frame, text="From:", font=('Leelawadee', 10)).pack(pady=(0, 5))
        self.start_date = DateEntry(
            from_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='y-mm-dd',
            font=('Leelawadee', 10)
        )
        self.start_date.pack()
        
        to_frame = ttk.Frame(date_controls)
        to_frame.pack(side='left', padx=20)
        ttk.Label(to_frame, text="To:", font=('Leelawadee', 10)).pack(pady=(0, 5))
        self.end_date = DateEntry(
            to_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='y-mm-dd',
            font=('Leelawadee', 10)
        )
        self.end_date.pack()
        
        reports_frame = ttk.LabelFrame(main_container, text="Available Reports", padding="15")
        reports_frame.pack(fill='both', expand=True, padx=10, pady=(0, 20))
        
        reports = [
            ("User Activity Report", "View detailed user activity and login statistics", self.generate_user_report),
            ("Print Jobs Report", "Track all printing activities and resource usage", self.generate_jobs_report),
            ("Stock Usage Report", "Monitor consumption of printer supplies", self.generate_stock_report),
            ("System Performance Report", "Analyze system metrics and performance data", self.generate_performance_report)
        ]
        
        for i, (report_name, description, command) in enumerate(reports):
            report_container = ttk.Frame(reports_frame)
            report_container.pack(fill='x', padx=10, pady=10)
            
            info_frame = ttk.Frame(report_container)
            info_frame.pack(side='left')
            
            ttk.Label(
                info_frame,
                text=report_name,
                font=('Leelawadee', 11, 'bold')
            ).pack(anchor='w')
            
            ttk.Label(
                info_frame,
                text=description,
                font=('Leelawadee', 9),
                foreground='gray'
            ).pack(anchor='w')
            
            generate_btn = ttk.Button(
                report_container,
                text="Generate Report",
                command=command,
                style='Action.TButton'
            )
            generate_btn.pack(side='right', pady=5)
            
            if i < len(reports) - 1:
                ttk.Separator(reports_frame, orient='horizontal').pack(fill='x', padx=10)
        
        
        style = ttk.Style()
        style.configure('Action.TButton', font=('Leelawadee', 10))
    def create_stock_tab(self, parent):
        """Create an enhanced stock management interface with improved layout and visual hierarchy"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=30, pady=20)

        style = ttk.Style()
        style.configure('Header.TLabel', font=('Leelawadee', 12, 'bold'))
        style.configure('SubHeader.TLabel', font=('Leelawadee', 10))
        style.configure('Action.TButton', font=('Leelawadee', 10, 'bold'))
        style.configure('Stock.TLabelframe', padding=20)
        style.configure('Stock.TLabelframe.Label', font=('Leelawadee', 11, 'bold'))

        stock_frame = ttk.LabelFrame(
            main_frame,
            text="Current Inventory Status",
            style='Stock.TLabelframe'
        )
        stock_frame.pack(fill='x', padx=5, pady=(0, 25))

        self.stock_labels = {}
        self.refresh_stock_display(stock_frame)

        add_stock_frame = ttk.LabelFrame(
            main_frame,
            text="Add New Inventory",
            style='Stock.TLabelframe'
        )
        add_stock_frame.pack(fill='x', padx=5)

        form_frame = ttk.Frame(add_stock_frame)
        form_frame.pack(fill='x', padx=25, pady=15)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(
            form_frame,
            text="Item Type:",
            style='SubHeader.TLabel'
        ).grid(row=0, column=0, sticky='w', padx=(0, 15), pady=8)

        item_type_var = tk.StringVar(value="paper")
        item_type_combo = ttk.Combobox(
            form_frame,
            textvariable=item_type_var,
            values=["paper", "file", "envelope"],
            state="readonly",
            width=35
        )
        item_type_combo.grid(row=0, column=1, sticky='ew', pady=8)

        unit_frame = ttk.Frame(form_frame)
        unit_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=8)
        unit_frame.columnconfigure(1, weight=1)

        ttk.Label(
            unit_frame,
            text="Unit Type:",
            style='SubHeader.TLabel'
        ).grid(row=0, column=0, sticky='w', padx=(0, 15))

        unit_type_var = tk.StringVar(value="rim")
        self.unit_type_combo = ttk.Combobox(
            unit_frame,
            textvariable=unit_type_var,
            values=["box", "rim"],
            state="readonly",
            width=35
        )
        self.unit_type_combo.grid(row=0, column=1, sticky='ew')

        ttk.Label(
            form_frame,
            text="Quantity:",
            style='SubHeader.TLabel'
        ).grid(row=2, column=0, sticky='w', padx=(0, 15), pady=8)

        quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(
            form_frame,
            textvariable=quantity_var,
            width=37
        )
        quantity_entry.grid(row=2, column=1, sticky='ew', pady=8)

        def validate_quantity(P):
            if P == "":
                return True
            try:
                value = int(P)
                return value > 0
            except ValueError:
                return False

        vcmd = (parent.register(validate_quantity), '%P')
        quantity_entry.configure(validate='key', validatecommand=vcmd)

        def on_item_type_change(*args):
            if item_type_var.get() == "paper":
                unit_frame.grid()
            else:
                unit_frame.grid_remove()

        item_type_var.trace('w', on_item_type_change)

        def add_stock():
            try:
                quantity = int(quantity_var.get())
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")

                success = self.service.inventory_model.add_stock(
                    item_type_var.get(),
                    quantity,
                    unit_type_var.get() if item_type_var.get() == "paper" else None
                )

                if success:
                    messagebox.showinfo(
                        "Success",
                        f"Successfully added {quantity} {unit_type_var.get() if item_type_var.get() == 'paper' else 'units'} of {item_type_var.get()}"
                    )
                    quantity_var.set("")
                    for widget in stock_frame.winfo_children():
                        widget.destroy()
                    self.refresh_stock_display(stock_frame)
                else:
                    messagebox.showerror("Error", "Failed to add stock")

            except ValueError as e:
                messagebox.showerror("Error", str(e))

        button_frame = ttk.Frame(add_stock_frame)
        button_frame.pack(fill='x', pady=(5, 10))

        add_button = ttk.Button(
            button_frame,
            text="Add to Inventory",
            command=add_stock,
            style='Action.TButton',
            width=25
        )
        add_button.pack(pady=(10, 0))

    def create_settings_tab(self, parent):
        """Create settings interface"""
        settings_frame = ttk.Frame(parent, padding="10")
        settings_frame.pack(fill='both', expand=True)
        
        backup_frame = ttk.LabelFrame(settings_frame, text="Backup & Maintenance", padding="10")
        backup_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Button(backup_frame, text="Backup Now", command=self.backup_system).pack(pady=5)
        ttk.Button(backup_frame, text="Clear Cache", command=self.clear_cache).pack(pady=5)
        ttk.Button(backup_frame, text="System Check", command=self.system_check).pack(pady=5)

    def show_create_user_dialog(self):
        """Show dialog for creating a new user"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New User")
        dialog.geometry("300x400")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill='both', expand=True)

        fields = {
            'Username': tk.StringVar(),
            'Password': tk.StringVar(),
            'Role': tk.StringVar(value='user'),
            'Full Name': tk.StringVar()
        }

        for field, var in fields.items():
            ttk.Label(frame, text=field).pack()
            if field == 'Password':
                ttk.Entry(frame, textvariable=var, show='*').pack()
            elif field == 'Role':
                ttk.Combobox(
                    frame, 
                    textvariable=var, 
                    values=['user', 'admin']
                ).pack()
            else:
                ttk.Entry(frame, textvariable=var).pack()

        def save_user():
            success = self.auth_manager.register_user(
                username=fields['Username'].get(),
                password=fields['Password'].get(),
                role=fields['Role'].get(),
                full_name=fields['Full Name'].get(),
                created_by=self.auth_manager.current_user.username
            )
            
            if success:
                messagebox.showinfo("Success", "User created successfully")
                self.refresh_users_list()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to create user")

        ttk.Button(
            frame,
            text="Create User",
            command=save_user
        ).pack(pady=20)

    def refresh_users_list(self):
        """Refresh the users table"""
        for item in self.users_table.get_children():
            self.users_table.delete(item)
        
        for user in self.auth_manager.get_all_users():
            self.users_table.insert('', 'end', values=user)

    def refresh_stock_display(self, stock_frame):
        """Refresh the stock level display"""
        for widget in stock_frame.winfo_children():
            widget.destroy()
        
        stock = self.service.inventory_model.get_stock()
        
        if 'paper' in stock:
            paper = stock['paper']
            current_sheets = paper['total_sheets']
            boxes = paper['boxes']
            rims = paper['rims']
            
            sheets = paper['sheets']
            
            paper_text = f"Paper: {boxes} boxes, {rims} rims, {current_sheets} sheets"
            
            ttk.Label(stock_frame, text=paper_text).pack(anchor='w', padx=5, pady=2)
        
        for item in ['file', 'envelope']:
            if item in stock:
                text = f"{item.capitalize()}s: {stock[item]['quantity']} units"
                ttk.Label(stock_frame, text=text).pack(anchor='w', padx=5, pady=2)

    def change_theme(self, event=None):
        """Handle theme change"""
        theme = self.current_theme.get()
        if theme == "dark":
            self.style.configure(".", background="gray20", foreground="white")
            self.style.configure("TNotebook", background="gray20")
            self.style.configure("TFrame", background="gray20")
        else:
            self.style.configure(".", background="white", foreground="black")
            self.style.configure("TNotebook", background="white")
            self.style.configure("TFrame", background="white")
        
        self.update_status(f"Theme changed to {theme}")

    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.config(text=message)

    def backup_system(self):
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
            
            self.service.export_data()
            
            import shutil
            shutil.copy2('printshop.db', f'{backup_path}_db.sqlite')
            
            self.update_status("Backup completed successfully")
            messagebox.showinfo("Success", "System backup completed successfully")
            
        except Exception as e:
            self.update_status("Backup failed")
            messagebox.showerror("Error", f"Backup failed: {str(e)}")

    def clear_cache(self):
        try:
            temp_dirs = ['reports', 'exports', 'temp']
            for dir_name in temp_dirs:
                if os.path.exists(dir_name):
                    for file in os.listdir(dir_name):
                        file_path = os.path.join(dir_name, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
            
            self.service.db.cursor.execute("DELETE FROM paper_stock_log")
            self.service.db.conn.commit()
            
            self.update_status("Cache cleared successfully")
            messagebox.showinfo("Success", "System cache cleared successfully")
        
        except Exception as e:
            self.update_status("Cache clearing failed")
            messagebox.showerror("Error", f"Failed to clear cache: {str(e)}")

    def system_check(self):
        """Perform comprehensive system health check"""
        try:
            self.update_status("Running system check...")
            checks = {}
            
            try:
                self.service.db.cursor.execute("SELECT 1")
                checks['Database Connection'] = ('OK', 'Database is responding normally')
            except sqlite3.Error as e:
                checks['Database Connection'] = ('ERROR', f'Database error: {str(e)}')
            
            try:
                db_size = os.path.getsize('printshop.db') / (1024 * 1024)
                checks['Database Size'] = (
                    'OK' if db_size < 100 else 'WARNING',
                    f'Current size: {db_size:.2f} MB'
                )
            except OSError as e:
                checks['Database Size'] = ('ERROR', f'Unable to check database size: {str(e)}')
            
            try:
                if hasattr(os, 'statvfs'):  
                    stat = os.statvfs('/')
                    free = (stat.f_bavail * stat.f_frsize) / (1024 * 1024 * 1024)  
                    total = (stat.f_blocks * stat.f_frsize) / (1024 * 1024 * 1024)  
                    used_percent = ((total - free) / total) * 100
                else: 
                    import ctypes
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p('.'), None, ctypes.pointer(total_bytes), 
                        ctypes.pointer(free_bytes)
                    )
                    total = total_bytes.value / (1024 * 1024 * 1024)  
                    free = free_bytes.value / (1024 * 1024 * 1024) 
                    used_percent = ((total - free) / total) * 100
                
                status = 'OK' if used_percent < 90 else 'WARNING' if used_percent < 95 else 'CRITICAL'
                checks['Disk Space'] = (status, f'Used: {used_percent:.1f}%, Free: {free:.1f} GB')
            except Exception as e:
                checks['Disk Space'] = ('ERROR', f'Unable to check disk space: {str(e)}')
            
        
            try:
                stock = self.service.inventory_model.get_stock()
                stock_status = []
                
                if 'paper' in stock:
                    sheets = stock['paper']['total_sheets']
                    if sheets < self.service.stock_thresholds['paper']:
                        stock_status.append(f'Paper low: {sheets} sheets')
                        
                if 'file' in stock:
                    files = stock['file']['quantity']
                    if files < self.service.stock_thresholds['file']:
                        stock_status.append(f'Files low: {files} units')
                        
                if 'envelope' in stock:
                    envelopes = stock['envelope']['quantity']
                    if envelopes < self.service.stock_thresholds['envelope']:
                        stock_status.append(f'Envelopes low: {envelopes} units')
                
                if stock_status:
                    checks['Stock Levels'] = ('WARNING', ', '.join(stock_status))
                else:
                    checks['Stock Levels'] = ('OK', 'All stock levels are adequate')
            except Exception as e:
                checks['Stock Levels'] = ('ERROR', f'Unable to check stock levels: {str(e)}')
        
            try:
                self.service.db.cursor.execute("PRAGMA integrity_check")
                result = self.service.db.cursor.fetchone()[0]
                checks['Database Integrity'] = (
                    'OK' if result == 'ok' else 'ERROR',
                    'Database integrity verified' if result == 'ok' else f'Integrity check failed: {result}'
                )
            except sqlite3.Error as e:
                checks['Database Integrity'] = ('ERROR', f'Integrity check failed: {str(e)}')
            
            try:
                report_dirs = ['reports', 'exports', 'backups']
                missing_dirs = []
                for dir_name in report_dirs:
                    if not os.path.exists(dir_name):
                        missing_dirs.append(dir_name)
                        try:
                            os.makedirs(dir_name)
                        except OSError:
                            pass
                
                if missing_dirs:
                    checks['Directories'] = ('WARNING', f'Created missing directories: {", ".join(missing_dirs)}')
                else:
                    checks['Directories'] = ('OK', 'All required directories present')
            except Exception as e:
                checks['Directories'] = ('ERROR', f'Directory check failed: {str(e)}')
            
            check_window = tk.Toplevel(self.root)
            check_window.title("System Health Check Results")
            check_window.geometry("600x400")
        
            frame = ttk.Frame(check_window)
            frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            canvas = tk.Canvas(frame)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            for check_name, (status, message) in checks.items():
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill='x', pady=5)
                
                color = {
                    'OK': 'green',
                    'WARNING': 'orange',
                    'ERROR': 'red',
                    'CRITICAL': 'red'
                }.get(status, 'black')
                
                ttk.Label(
                    frame, 
                    text=check_name, 
                    font=('Leelawadee', 10, 'bold')
                ).pack(side='left')
                
                ttk.Label(
                    frame,
                    text=f"[{status}]",
                    foreground=color
                ).pack(side='left', padx=5)
                
                ttk.Label(
                    frame,
                    text=message,
                    wraplength=400
                ).pack(side='left', padx=5)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            overall_status = 'ERROR' if any(status == 'ERROR' for status, _ in checks.values()) else \
                            'WARNING' if any(status == 'WARNING' for status, _ in checks.values()) else 'OK'
            
            self.update_status(f"System check completed: {overall_status}")
            
        except Exception as e:
            self.update_status("System check failed")
            messagebox.showerror("Error", f"System check failed: {str(e)}")
    
    def generate_user_report(self):
        """Generate user activity report"""
        try:
            start = self.start_date.get_date()
            end = self.end_date.get_date()
            
            report_dir = "reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            filename = os.path.join(report_dir, f"user_activity_{start}_{end}.txt")
            
            with open(filename, 'w') as f:
                f.write(f"User Activity Report ({start} to {end})\n")
                f.write("="*50 + "\n\n")
                
                users = self.auth_manager.get_all_users()
                
                for user in users:
                    username = user[0]
                    f.write(f"\nUser: {username}\n")
                    f.write("-"*20 + "\n")
                    
                    self.service.db.cursor.execute('''
                        SELECT COUNT(*), SUM(amount)
                        FROM transactions
                        WHERE date BETWEEN ? AND ?
                        AND created_by = ?
                    ''', (start, end, username))
                    
                    count, total = self.service.db.cursor.fetchone()
                    count = count or 0
                    total = total or 0
                    
                    f.write(f"Total Transactions: {count}\n")
                    f.write(f"Total Amount: M{total:.2f}\n")
                    
                    self.service.db.cursor.execute('''
                        SELECT service, COUNT(*)
                        FROM transactions
                        WHERE date BETWEEN ? AND ?
                        AND created_by = ?
                        GROUP BY service
                    ''', (start, end, username))
                    
                    f.write("\nService Breakdown:\n")
                    for service, service_count in self.service.db.cursor.fetchall():
                        f.write(f"{service}: {service_count}\n")
            
            self.update_status("User report generated successfully")
            messagebox.showinfo("Success", f"Report generated: {filename}")
            
        except Exception as e:
            self.update_status("Report generation failed")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def generate_jobs_report(self):
        """Generate print jobs report"""
        try:
            start = self.start_date.get_date()
            end = self.end_date.get_date()
            
            report_dir = "reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            filename = os.path.join(report_dir, f"print_jobs_{start}_{end}.txt")
            
            with open(filename, 'w') as f:
                f.write(f"Print Jobs Report ({start} to {end})\n")
                f.write("="*50 + "\n\n")
                
                self.service.db.cursor.execute('''
                    SELECT COUNT(*), SUM(amount), SUM(papers_used)
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                ''', (start, end))
                
                count, total, papers = self.service.db.cursor.fetchone()
                count = count or 0
                total = total or 0
                papers = papers or 0
                
                f.write("Overall Summary:\n")
                f.write(f"Total Jobs: {count}\n")
                f.write(f"Total Revenue: M{total:.2f}\n")
                f.write(f"Total Papers Used: {papers}\n\n")
                
                f.write("Service Breakdown:\n")
                f.write("-"*20 + "\n")
                
                self.service.db.cursor.execute('''
                    SELECT service, 
                           COUNT(*) as job_count,
                           SUM(amount) as total_amount,
                           SUM(papers_used) as total_papers
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                    GROUP BY service
                ''', (start, end))
                
                for service, job_count, service_total, service_papers in self.service.db.cursor.fetchall():
                    f.write(f"\nService: {service}\n")
                    f.write(f"Number of Jobs: {job_count}\n")
                    f.write(f"Total Revenue: M{service_total:.2f}\n")
                    f.write(f"Papers Used: {service_papers or 0}\n")
            
            self.update_status("Jobs report generated successfully")
            messagebox.showinfo("Success", f"Report generated: {filename}")
            
        except Exception as e:
            self.update_status("Report generation failed")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def generate_stock_report(self):
        """Generate stock usage report"""
        try:
            start = self.start_date.get_date()
            end = self.end_date.get_date()
            
            report_dir = "reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            filename = os.path.join(report_dir, f"stock_usage_{start}_{end}.txt")
            
            with open(filename, 'w') as f:
                f.write(f"Stock Usage Report ({start} to {end})\n")
                f.write("="*50 + "\n\n")
                
                current_stock = self.service.inventory_model.get_stock()
                
                f.write("Current Stock Levels:\n")
                f.write("-"*20 + "\n")
                
                if 'paper' in current_stock:
                    paper = current_stock['paper']
                    f.write(f"Paper: {paper['boxes']} boxes, {paper['rims']} rims, {paper['sheets']} sheets\n")
                    f.write(f"Total Sheets: {paper['total_sheets']}\n")
                
                for item in ['file', 'envelope']:
                    if item in current_stock:
                        f.write(f"{item.capitalize()}: {current_stock[item]['quantity']} units\n")
                
                f.write("\nUsage Statistics:\n")
                f.write("-"*20 + "\n")
                
                self.service.db.cursor.execute('''
                    SELECT SUM(papers_used)
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                ''', (start, end))
                
                total_papers = self.service.db.cursor.fetchone()[0] or 0
                f.write(f"\nTotal Papers Used: {total_papers} sheets\n")
                
                for item in ['File', 'Envelope']:
                    self.service.db.cursor.execute('''
                        SELECT COUNT(*)
                        FROM transactions
                        WHERE date BETWEEN ? AND ?
                        AND service = ?
                    ''', (start, end, item))
                    
                    count = self.service.db.cursor.fetchone()[0] or 0
                    f.write(f"{item}s Used: {count} units\n")
                
                f.write("\nStock Additions:\n")
                f.write("-"*20 + "\n")
                
                self.service.db.cursor.execute('''
                    SELECT date, quantity_added
                    FROM paper_stock_log
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date
                ''', (start, end))
                
                for date, quantity in self.service.db.cursor.fetchall():
                    f.write(f"{date}: Added {quantity} sheets\n")
            
            self.update_status("Stock report generated successfully")
            messagebox.showinfo("Success", f"Report generated: {filename}")
            
        except Exception as e:
            self.update_status("Report generation failed")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def generate_performance_report(self):
        """Generate system performance report"""
        try:
            start = self.start_date.get_date()
            end = self.end_date.get_date()
            
            report_dir = "reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            filename = os.path.join(report_dir, f"performance_{start}_{end}.txt")
            
            with open(filename, 'w') as f:
                f.write(f"System Performance Report ({start} to {end})\n")
                f.write("="*50 + "\n\n")
                
                f.write("Daily Transaction Statistics:\n")
                f.write("-"*20 + "\n")
                
                self.service.db.cursor.execute('''
                    SELECT date,
                        COUNT(*) as transaction_count,
                        SUM(amount) as daily_revenue,
                        COUNT(DISTINCT created_by) as active_users
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                    GROUP BY date
                    ORDER BY date
                ''', (start, end))
                
                total_days = 0
                total_transactions = 0
                total_revenue = 0
            
                
                for date, count, revenue, users in self.service.db.cursor.fetchall():
                    f.write(f"\nDate: {date}\n")
                    f.write(f"Transactions: {count}\n")
                    f.write(f"Revenue: M{revenue:.2f}\n")
                   
                    
                    total_days += 1
                    total_transactions += count
                    total_revenue += revenue
                   
                
                if total_days > 0:
                    f.write("\nAverages:\n")
                    f.write(f"Daily Transactions: {total_transactions/total_days:.1f}\n")
                    f.write(f"Daily Revenue: M{total_revenue/total_days:.2f}\n")
                   
                
                f.write("\nPeak Usage Hours:\n")
                f.write("-"*20 + "\n")
                
                self.service.db.cursor.execute('''
                    SELECT strftime('%H', timestamp) as hour,
                        COUNT(*) as transaction_count
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                    GROUP BY hour
                    ORDER BY transaction_count DESC
                    LIMIT 5
                ''', (start, end))
                
                for hour, count in self.service.db.cursor.fetchall():
                    f.write(f"{hour}:00 - {count} transactions\n")
                
                f.write("\nService Popularity:\n")
                f.write("-"*20 + "\n")
                
                self.service.db.cursor.execute('''
                    SELECT service,
                        COUNT(*) as usage_count,
                        SUM(amount) as total_revenue
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                    GROUP BY service
                    ORDER BY usage_count DESC
                ''', (start, end))
                
                for service, count, revenue in self.service.db.cursor.fetchall():
                    f.write(f"{service}:\n")
                    f.write(f"Usage Count: {count}\n")
                    f.write(f"Revenue: M{revenue:.2f}\n")
                    
                f.write("\nSystem Health:\n")
                f.write("-"*20 + "\n")
                
                db_size = os.path.getsize('printshop.db') / (1024 * 1024)  
                f.write(f"Database Size: {db_size:.2f} MB\n")
                
                try:
                    if hasattr(os, 'statvfs'): 
                        stat = os.statvfs('/')
                        free = (stat.f_bavail * stat.f_frsize) / (1024 * 1024 * 1024)  
                        total = (stat.f_blocks * stat.f_frsize) / (1024 * 1024 * 1024)  
                        used_percent = ((total - free) / total) * 100
                    else:  
                        import ctypes
                        free_bytes = ctypes.c_ulonglong(0)
                        total_bytes = ctypes.c_ulonglong(0)
                        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                            ctypes.c_wchar_p('.'), None, ctypes.pointer(total_bytes), 
                            ctypes.pointer(free_bytes)
                        )
                        total = total_bytes.value / (1024 * 1024 * 1024)  
                        free = free_bytes.value / (1024 * 1024 * 1024)  
                        used_percent = ((total - free) / total) * 100
                    
                    f.write(f"Disk Space Used: {used_percent:.1f}%\n")
                    f.write(f"Free Space: {free:.1f} GB\n")
                except Exception as disk_error:
                    f.write(f"Disk Space Check Error: {str(disk_error)}\n")
                
                low_stock_items = []
                stock = self.service.inventory_model.get_stock()
                
                if 'paper' in stock and stock['paper']['total_sheets'] < self.service.stock_thresholds['paper']:
                    low_stock_items.append('Paper')
                if 'file' in stock and stock['file']['quantity'] < self.service.stock_thresholds['file']:
                    low_stock_items.append('Files')
                if 'envelope' in stock and stock['envelope']['quantity'] < self.service.stock_thresholds['envelope']:
                    low_stock_items.append('Envelopes')
                
                if low_stock_items:
                    f.write("\nLow Stock Warnings:\n")
                    for item in low_stock_items:
                        f.write(f"- {item}\n")
            
            self.update_status("Performance report generated successfully")
            messagebox.showinfo("Success", f"Report generated: {filename}")
                    
        except Exception as e:
            self.update_status("Report generation failed")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
    
    def get_low_stock_count(self):
        """Count items with low stock levels"""
        low_count = 0
        stock = self.service.inventory_model.get_stock()
        
        if 'paper' in stock:
            if stock['paper']['total_sheets'] < 1000:  
                low_count += 1
        
        for item in ['file', 'envelope']:
            if item in stock:
                if stock[item]['quantity'] < 50: 
                    low_count += 1
        
        return low_count
    def logout(self):
        """Handle logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            try:
                self.service.db.conn.commit()
                self.root.withdraw()
                self.root.quit()
                from login_ui import LoginUI
                LoginUI(self.root, self.auth_manager, lambda: self.root.deiconify())
                
            except Exception as e:
                messagebox.showerror("Error", f"Error during logout: {str(e)}")
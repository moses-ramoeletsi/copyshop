import csv
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkinter import filedialog
from PIL import Image, ImageTk

class PrintShopUI:
    def __init__(self, root, service, auth_manager):
        self.root = root
        self.service = service
        self.auth_manager = auth_manager
        self.root.title("AlphaPrinting Management System")
        self.root.state('zoomed')
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.paper_stock = tk.IntVar()
        self.file_stock = tk.IntVar()
        self.envelope_stock = tk.IntVar()
        self.total_revenue = tk.DoubleVar()
        self.papers_used = tk.IntVar()
        
        self.load_initial_data()
        self.create_ui()
        self.update_displays()

        self.export_button = None

    def create_main_container(self):
        """Create main scrollable container"""
        self.main_canvas = tk.Canvas(self.root)
        self.main_canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        self.scrollable_frame.pack(expand=True, fill='both')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.root.winfo_width())
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.root.bind('<Configure>', self._on_window_configure)

    def _on_window_configure(self, event):
        """Update canvas width when window is resized"""
        if event.widget == self.root:
            canvas_width = event.width - 20
            self.main_canvas.itemconfig(1, width=canvas_width)
                              
    def load_initial_data(self):
        """Load initial data from service"""
        self.update_stock_variables()
        daily_total, papers = self.service.get_daily_summary()
        self.total_revenue.set(daily_total)
        self.papers_used.set(papers)

    def update_stock_variables(self):
        """Update stock variables from inventory"""
        self.paper_stock.set(self.service.inventory_model.get_stock('paper'))
        self.file_stock.set(self.service.inventory_model.get_stock('file'))
        self.envelope_stock.set(self.service.inventory_model.get_stock('envelope'))

    def create_ui(self):
        """Create main UI components"""
        self.create_main_container()
        self.create_header()
        self.configure_styles()
        self.setup_main_grid()
        self.create_daily_summary()
        self.create_quick_actions()
        self.create_service_summary()
        self.create_transactions()
        self.create_daily_records()

    def create_header(self):
        """Create header section with empty state handling"""
        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.pack(fill='x', padx=20, pady=(10, 5))

        left_section = ttk.Frame(header_frame)
        left_section.pack(side='left', fill='y')

        logo_frame = ttk.Frame(left_section)
        logo_frame.pack(side='top', anchor='w')

        logo_label = ttk.Label(
            logo_frame,
            text="AlphaPrinting",
            font=('Leelawadee', 26, 'bold'),
            foreground='#1e40af' 
        )
        logo_label.pack(side='top')

        if hasattr(self.auth_manager, 'current_user') and self.auth_manager.current_user:
            user_frame = ttk.Frame(left_section)
            user_frame.pack(side='top', anchor='w', pady=(6, 0))

            user_label = ttk.Label(
                user_frame,
                text=f"Welcome, {self.auth_manager.current_user.username}",
                font=('Leelawadee', 12, 'bold'),
                foreground='#4b5563' 
            )
            user_label.pack(side='left')

        center_section = ttk.Frame(header_frame)
        center_section.pack(side='left', fill='both', expand=True, padx=40)

        stock_label = ttk.Label(
            center_section,
            text="Current Stock",
            font=('Leelawadee', 12, 'bold'),
            foreground='#1f2937'
        )
        stock_label.pack(pady=(0, 10))

        stock_container = ttk.Frame(center_section)
        stock_container.pack(fill='x')

        self.stock_labels = {}
        stock_items = [
            ('paper', '📄 Paper', '#3b82f6'),
            ('file', '📁 Files', '#16a34a'),
            ('envelope', '✉️ Envelopes', '#8b5cf6')
        ]

        for item, label, color in stock_items:
            stock_frame = ttk.Frame(stock_container, style='StockFrame.TFrame')
            stock_frame.pack(side='left', padx=10, fill='x', expand=True)

            header_label = ttk.Label(
                stock_frame,
                text=label,
                font=('Leelawadee', 10, 'bold'),
                foreground='#6b7280'
            )
            header_label.pack(anchor='w')

            stock_value = self.get_stock_value(item)
            if stock_value is None or stock_value == 0:
                label_text = "No stock data"
                label_color = '#94a3b8'  
            else:
                if item == 'paper':
                    label_text = f"{stock_value} sheets"
                else:
                    label_text = str(stock_value)
                label_color = color

            self.stock_labels[item] = ttk.Label(
                stock_frame,
                text=label_text,
                font=('Leelawadee', 12, 'bold'),
                foreground=label_color
            )
            self.stock_labels[item].pack(anchor='w')

        right_section = ttk.Frame(header_frame)
        right_section.pack(side='right', fill='y')
        
        style = ttk.Style()
        style.configure(
            'Header.TButton',
            font=('Leelawadee', 11, 'bold'),
            padding=(20, 10), 
            width=15,      
        )

        button_configs = [
            ("Refresh", "🔄", self.refresh_page),
            ("Record Expense", "💰", self.show_expense_dialog),
            ("End Day", "🔚", self.end_day),
            ("Logout", "🚪", self.logout)
        ]

        buttons_container = ttk.Frame(right_section)
        buttons_container.pack(pady=5)

        for text, icon, command in button_configs:
            btn_frame = ttk.Frame(buttons_container)
            btn_frame.pack(pady=2, padx=5) 
            
            btn = ttk.Button(
                btn_frame,
                text=f"{icon} {text}",
                command=command,
                style='Header.TButton'
            )
            btn.pack(expand=True, fill='both')
            
            if text == "End Day":
                self.end_day_button_frame = btn_frame

        separator = ttk.Separator(self.scrollable_frame, orient='horizontal')
        separator.pack(fill='x', padx=20, pady=(5, 0))
        
   
    
    def get_stock_value(self, item_type):
        """Get stock value with error handling"""
        try:
            if item_type == 'paper':
                return self.paper_stock.get()
            elif item_type == 'file':
                return self.file_stock.get()
            elif item_type == 'envelope':
                return self.envelope_stock.get()
            return None
        except (AttributeError, tk.TclError):
            return None
        
    def setup_main_grid(self):
        """Setup the main grid layout for the application"""
        self.main_container = ttk.Frame(self.scrollable_frame)
        self.main_container.pack(fill='both', expand=True, padx=20, pady=15)
        
        self.main_container.columnconfigure(0, weight=6)          
        self.main_container.columnconfigure(1, weight=4)  
    def create_quick_actions(self):
        """Create quick actions panel on the left"""
        actions_frame = ttk.LabelFrame(
            self.main_container,
            text="Quick Actions",
            padding="20"
        )
        actions_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

        services_grid = ttk.Frame(actions_frame)
        services_grid.pack(fill='both', expand=True)

        for i in range(3):
            services_grid.columnconfigure(i, weight=1)

        services = [
            ("Photocopy", "📄", "#3b82f6"),
            ("Printing", "🖨️", "#16a34a"),
            ("Scanning", "📱", "#8b5cf6"),
            ("Lamination", "📑", "#ea580c"),
            ("File", "📁", "#0891b2"),
            ("Envelope", "✉️", "#db2777")
        ]

        for i, (service, icon, color) in enumerate(services):
            service_frame = ttk.Frame(services_grid, style='Service.TFrame')
            service_frame.grid(
                row=i//3,
                column=i%3,
                padx=5,
                pady=5,
                sticky='nsew'
            )
            
            btn = ttk.Button(
                service_frame,
                text=f"{icon}\n{service}",
                style='Service.TButton',
                command=lambda s=service: self.show_service_dialog(s)
            )
            btn.pack(fill='both', expand=True, padx=5, pady=5)

    def create_daily_summary(self):
        """Create daily summary panel on the right"""
        summary_frame = ttk.LabelFrame(
            self.main_container,
            text="Daily Summary",
            padding="20"
        )
        summary_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))

        summary_frame.columnconfigure(0, weight=1)
        
        revenue_card = ttk.Frame(summary_frame, style='Card.TFrame')
        revenue_card.grid(row=0, column=0, pady=(0, 10), sticky='ew')
        
        ttk.Label(
            revenue_card,
            text="Total Revenue",
            font=('Leelawadee', 12),
            style='CardTitle.TLabel'
        ).pack(pady=(5, 0))
        
        self.revenue_label = ttk.Label(
            revenue_card,
            text=f"M{self.total_revenue.get():.2f}",
            font=('Leelawadee', 32, 'bold'),
            style='CardValue.TLabel'
        )
        self.revenue_label.pack(pady=(5, 10))

        papers_card = ttk.Frame(summary_frame, style='Card.TFrame')
        papers_card.grid(row=1, column=0, sticky='ew')
        
        ttk.Label(
            papers_card,
            text="Papers Used",
            font=('Leelawadee', 12),
            style='CardTitle.TLabel'
        ).pack(pady=(5, 0))
        
        self.papers_used_label = ttk.Label(
            papers_card,
            text=str(self.papers_used.get()),
            font=('Leelawadee', 32, 'bold'),
            style='CardValue.TLabel'
        )
        self.papers_used_label.pack(pady=(5, 10))

    def configure_styles(self):
        """Configure custom styles for the UI components"""
        style = ttk.Style()
        style.configure('Card.TFrame', 
                    background='#ffffff',
                    relief='solid',
                    borderwidth=1)
        
        style.configure('CardTitle.TLabel',
                    background='#ffffff',
                    foreground='#4b5563')
        
        style.configure('CardValue.TLabel',
                    background='#ffffff',
                    foreground='#111827')
        
        style.configure('Service.TFrame',
                    relief='solid',
                    borderwidth=1)
        
        style.configure('Service.TButton',
                    padding=15,
                    font=('Leelawadee', 11, 'bold'))

    def update_summary(self):
        """Update the summary labels with current values"""
        self.revenue_label.config(text=f"M{self.total_revenue.get():.2f}")
        self.papers_used_label.config(text=str(self.papers_used.get()))
    
    def create_service_summary(self):
        """Create service summary section"""
        service_frame = ttk.LabelFrame(self.scrollable_frame, text="Service Summary", padding="10")
        service_frame.pack(fill='x', padx=20, pady=5)
        
        self.service_labels = {}
        for i, service in enumerate(self.service.prices.keys()):
            frame = ttk.Frame(service_frame)
            frame.grid(row=0, column=i, padx=10, sticky='nsew')
            
            ttk.Label(frame, text=service, font=('Leelawadee', 10, 'bold')).pack()
            
            self.service_labels[service] = {
                'count': ttk.Label(frame, text="Count: 0"),
                'amount': ttk.Label(frame, text="M0.00")
            }
            
            self.service_labels[service]['count'].pack()
            self.service_labels[service]['amount'].pack()
            
            service_frame.grid_columnconfigure(i, weight=1)

    def create_transactions(self):
        """Create recent transactions section"""
        trans_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="Recent Transactions",
            padding="10"
        )
        trans_frame.pack(fill='x', padx=20, pady=5)
        
        header_frame = ttk.Frame(trans_frame)
        header_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(
            header_frame,
            text="Today's Transactions",
            font=('Leelawadee', 12, 'bold'),
            foreground='#1e40af'
        ).pack(side='left')
        
        columns = ('Time', 'Service', 'Quantity', 'Papers', 'Amount')
        self.transaction_tree = ttk.Treeview(
            trans_frame,
            columns=columns,
            show='headings',
            height=5
        )
        
        column_widths = {
            'Time': 100,
            'Service': 150,
            'Quantity': 100,
            'Papers': 100,
            'Amount': 100
        }
        
        for col in columns:
            self.transaction_tree.heading(col, text=col)
            self.transaction_tree.column(col, width=column_widths[col])
        
        v_scrollbar = ttk.Scrollbar(
            trans_frame,
            orient="vertical",
            command=self.transaction_tree.yview
        )
        self.transaction_tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.transaction_tree.pack(side='left', fill='x', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        
        style = ttk.Style()
        style.configure("Treeview", font=('Leelawadee', 10))
        style.configure("Treeview.Heading", font=('Leelawadee', 10, 'bold'))

   

    def create_daily_records(self):
        """Create daily records section"""
        records_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="Daily Records",
            padding="10"
        )
        records_frame.pack(fill='x', padx=20, pady=5)
        
        header_frame = ttk.Frame(records_frame)
        header_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(
            header_frame,
            text="Financial Summary",
            font=('Leelawadee', 12, 'bold'),
            foreground='#1e40af'
        ).pack(side='left')
        
        columns = (
            'Day',
            'Daily Income',
            'Mottakase',
            'Pampiri',
            'INK/Cardrige',
            'Drawings',
            'Total Expenses',
            'Balance'
        )
        
        self.records_tree = ttk.Treeview(
            records_frame,
            columns=columns,
            show='headings',
            height=10
        )
        
        column_widths = {
            'Day': 100,
            'Daily Income': 120,
            'Mottakase': 100,
            'Pampiri': 100,
            'INK/Cardrige': 100,
            'Drawings': 100,
            'Total Expenses': 120,
            'Balance': 120
        }
        
        for col in columns:
            self.records_tree.heading(col, text=col)
            self.records_tree.column(col, width=column_widths[col])
        
        v_scrollbar = ttk.Scrollbar(
            records_frame,
            orient="vertical",
            command=self.records_tree.yview
        )
        
        h_scrollbar = ttk.Scrollbar(
            records_frame,
            orient="horizontal",
            command=self.records_tree.xview
        )
        
        self.records_tree.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        self.records_tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')

 
    def show_service_dialog(self, service):
        """Show dialog for new service transaction"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"New {service} Transaction")
        dialog.geometry("300x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        content_frame = ttk.Frame(dialog, padding="10")
        content_frame.pack(fill='both', expand=True)
        
        ttk.Label(content_frame, 
                 text=f"Price per {service}: M{self.service.prices[service]:.2f}",
                 font=('Leelawadee', 10, 'bold')).pack(pady=5)
        
        ttk.Label(content_frame, text="Quantity:", font=('Leelawadee')).pack(pady=5)
        qty_var = tk.StringVar(value="1")
        qty_entry = ttk.Entry(content_frame, textvariable=qty_var)
        qty_entry.pack(pady=5)
        
        papers_var = tk.StringVar(value="1")
        papers_label = None
        if service in ["Photocopy", "Printing"]:
            papers_label = ttk.Label(content_frame, text="Total papers: 0", font=('Leelawadee'))
            papers_label.pack(pady=5)
        
        total_label = ttk.Label(content_frame, text="Total: M0.00", font=('Leelawadee'))
        total_label.pack(pady=5)
        
        def update_total(*args):
            try:
                qty = int(qty_var.get())
                total = qty * self.service.prices[service]
                total_label.config(text=f"Total: M{total:.2f}")
                
                if service in ["Photocopy", "Printing"]:
                    papers = int(papers_var.get())
                    papers_label.config(text=f"Total papers: {qty * papers}")
            except ValueError:
                total_label.config(text="Total: M0.00")
                if papers_label:
                    papers_label.config(text="Total papers: 0")
        
        qty_var.trace('w', update_total)
        if papers_label:
            papers_var.trace('w', update_total)
        
        def process():
            try:
                qty = int(qty_var.get())
                papers = int(papers_var.get()) if service in ["Photocopy", "Printing"] else 0
                
                if qty <= 0 or (papers < 0 if papers else False):
                    messagebox.showerror("Error", "Please enter valid positive numbers")
                    return
                
                if service == "File" and qty > self.file_stock.get():
                    messagebox.showerror("Error", "Not enough files in stock!")
                    return
                elif service == "Envelope" and qty > self.envelope_stock.get():
                    messagebox.showerror("Error", "Not enough envelopes in stock!")
                    return
                elif papers > 0 and (qty * papers) > self.paper_stock.get():
                    messagebox.showerror("Error", "Not enough paper in stock!")
                    return
                self.service.process_transaction(service, qty, papers)
                
                self.update_stock_variables()
                
                dialog.destroy()
                self.update_displays()
                
                if papers > 0:
                    messagebox.showinfo("Success", 
                        f"Transaction processed!\nRemaining paper stock: {self.paper_stock.get()} sheets")
                elif service == "File":
                    messagebox.showinfo("Success", 
                        f"Transaction processed!\nRemaining files: {self.file_stock.get()}")
                elif service == "Envelope":
                    messagebox.showinfo("Success", 
                        f"Transaction processed!\nRemaining envelopes: {self.envelope_stock.get()}")
                else:
                    messagebox.showinfo("Success", "Transaction processed successfully!")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")
        
        ttk.Button(content_frame, text="Process", command=process).pack(pady=10)

    def show_expense_dialog(self):
        """Show dialog for recording expense"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Record Expense")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        content_frame = ttk.Frame(dialog, padding="10")
        content_frame.pack(fill='both', expand=True)
        
        ttk.Label(content_frame, text="Category:").pack(pady=5)
        categories = ['Mottakase', 'Pampiri', 'INK/Cardrige', 'Drawings']
        category_var = tk.StringVar(value=categories[0])
        category_menu = ttk.Combobox(content_frame,
                                   textvariable=category_var,
                                   values=categories,
                                   state='readonly')
        category_menu.pack(pady=5)
        
        ttk.Label(content_frame, text="Amount (M):").pack(pady=5)
        amount_var = tk.StringVar()
        amount_entry = ttk.Entry(content_frame, textvariable=amount_var)
        amount_entry.pack(pady=5)
        
        ttk.Label(content_frame, text="Description:").pack(pady=5)
        description_text = tk.Text(content_frame, height=4, width=40)
        description_text.pack(pady=5)
        
        def save():
            try:
                amount = float(amount_var.get())
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    return
                
                description = description_text.get("1.0", "end-1c")
                self.service.expense_model.add_expense(
                    category_var.get(),
                    amount,
                    description
                )
                
                dialog.destroy()
                self.update_displays()
                messagebox.showinfo("Success", f"Expense recorded: M{amount:.2f}")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")
        
        ttk.Button(content_frame, text="Save", command=save).pack(pady=10)
    
    def end_day(self):
        """Process end of day operations"""
        if not messagebox.askyesno("End Day",
                                 "Are you sure you want to end the day?\nThis will finalize all records for today."):
            return
        
        self.service.end_day()
        
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)
        
        self.total_revenue.set(0)
        self.papers_used.set(0)
        
        if not self.export_button:
            export_btn_frame = ttk.Frame(self.end_day_button_frame.master)
            export_btn_frame.pack(pady=2, padx=5)
            
            self.export_button = ttk.Button(
                export_btn_frame,
                text="📊 Export Data",
                command=self.service.export_data,
                style='Header.TButton'
            )
            self.export_button.pack(expand=True, fill='both')
        
        self.update_displays()
        messagebox.showinfo("Success", "Day ended successfully!\nDaily report has been generated.")
    def update_displays(self):
        for item in ['paper', 'file', 'envelope']:
            stock_value = self.get_stock_value(item)
            if stock_value is None or stock_value == 0:
                self.stock_labels[item].config(
                    text="No stock data",
                    foreground='#ab1123'
                )
            else:
                if item == 'paper':
                    self.stock_labels[item].config(
                        text=f"{stock_value} sheets",
                        foreground='#3b82f6'
                    )
                else:
                    self.stock_labels[item].config(
                        text=str(stock_value),
                        foreground='#16a34a' if item == 'file' else '#8b5cf6'
                    )
        
        try:
            daily_total, papers = self.service.get_daily_summary()
            self.revenue_label.config(text=f"M{daily_total:.2f}" if daily_total > 0 else "No revenue today")
            self.papers_used_label.config(text=str(papers) if papers > 0 else "No papers used")
        except:
            self.revenue_label.config(text="No revenue data")
            self.papers_used_label.config(text="No usage data")
        
        service_summary = self.service.get_service_summary()
        for service, data in service_summary.items():
            if data['count'] == 0 and data['amount'] == 0:
                self.service_labels[service]['count'].config(text="No transactions")
                self.service_labels[service]['amount'].config(text="---")
            else:
                self.service_labels[service]['count'].config(text=f"Count: {data['count']}")
                self.service_labels[service]['amount'].config(text=f"M{data['amount']:.2f}")
        
        self.update_transactions_tree()
        self.update_records_tree()
    def update_transactions_tree(self):
        """Update recent transactions display"""
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        self.service.db.cursor.execute('''
            SELECT timestamp, service, quantity, papers_used, amount 
            FROM transactions 
            WHERE date = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (today,))
        
        for trans in self.service.db.cursor.fetchall():
            time = datetime.strptime(trans[0], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
            values = (
                time,
                trans[1],
                trans[2],
                trans[3],
                f"M{trans[4]:.2f}"
            )
            self.transaction_tree.insert('', 'end', values=values)

    def update_records_tree(self):
        """Update daily records display"""
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)
        
        self.service.db.cursor.execute('''
            SELECT * FROM daily_records 
            ORDER BY date DESC 
            LIMIT 30
        ''')
        
        for record in self.service.db.cursor.fetchall():
            values = [
                record[0],  
                f"M{record[1]:.2f}",  
                f"M{record[2]:.2f}", 
                f"M{record[3]:.2f}", 
                f"M{record[4]:.2f}",  
                f"M{record[5]:.2f}",
                f"M{record[6]:.2f}", 
                f"M{record[7]:.2f}" 
            ]
            self.records_tree.insert('', 'end', values=values)
   
    def refresh_page(self):
        """Refresh all data and display elements on the page"""
        try:
            self.load_initial_data()
            
            self.update_stock_variables()
            
            self.update_displays()
            
            self.update_transactions_tree()
            
            self.update_records_tree()
            
            service_summary = self.service.get_service_summary()
            for service, data in service_summary.items():
                if service in self.service_labels:
                    if data['count'] == 0 and data['amount'] == 0:
                        self.service_labels[service]['count'].config(text="No transactions")
                        self.service_labels[service]['amount'].config(text="---")
                    else:
                        self.service_labels[service]['count'].config(text=f"Count: {data['count']}")
                        self.service_labels[service]['amount'].config(text=f"M{data['amount']:.2f}")
            
            messagebox.showinfo("Success", "Page refreshed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh page: {str(e)}")
    
    def logout(self):
        """Handle logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.withdraw()
            self.root.quit()
            from login_ui import LoginUI
            LoginUI(self.root, self.auth_manager, lambda: self.root.deiconify())
import tkinter as tk
from tkinter import ttk, messagebox
from admin import AdminDashboardUI
from auth import AuthManager
from login_ui import LoginUI
from models import DatabaseManager
from services import PrintShopService
from ui import PrintShopUI

def main():
    db_manager = DatabaseManager()
    auth_manager = AuthManager(db_manager)
    service = PrintShopService(db_manager)
    
    root = tk.Tk()
    
    def on_login_success():
        if auth_manager.is_admin():
            app = AdminDashboardUI(root, auth_manager, service)
        else:
            app = PrintShopUI(root, service, auth_manager)
        root.deiconify()
    login_window = LoginUI(root, auth_manager, on_login_success)
    root.withdraw()
    root.mainloop()

if __name__ == "__main__":
    main()
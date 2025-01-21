import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name='printshop.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.init_database()

    def init_database(self):
        """Initialize all database tables"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                date TEXT,
                service TEXT,
                quantity INTEGER,
                amount REAL,
                papers_used INTEGER,
                timestamp TEXT,
                created_by TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                item TEXT PRIMARY KEY,
                quantity INTEGER,
                last_updated TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_records (
                date TEXT PRIMARY KEY,
                daily_income REAL,
                mottakase REAL,
                pampiri REAL,
                ink_cardrige REAL,
                drawings REAL,
                total_expenses REAL,
                balance REAL,
                papers_used INTEGER
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                date TEXT,
                category TEXT,
                amount REAL,
                description TEXT,
                timestamp TEXT,
                created_by TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_stock_log (
                id INTEGER PRIMARY KEY,
                date TEXT,
                quantity_added INTEGER,
                timestamp TEXT,
                created_by TEXT
            )
        ''')
    
        self.cursor.execute('SELECT COUNT(*) FROM inventory')
        if self.cursor.fetchone()[0] == 0:
            initial_inventory = [
                ('paper', 0),
                ('file', 0),
                ('envelope', 0)
            ]
            self.cursor.executemany(
                'INSERT OR IGNORE INTO inventory (item, quantity, last_updated) VALUES (?, ?, ?)',
                [(item, qty, datetime.now().strftime('%Y-%m-%d %H:%M:%S')) 
                 for item, qty in initial_inventory]
            )
        
        self.conn.commit()

class Transaction:
    def __init__(self, db_manager):
        self.db = db_manager

    def add_transaction(self, service, quantity, amount, papers_used=0, created_by=None):
        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.db.cursor.execute('''
            INSERT INTO transactions 
            (date, service, quantity, amount, papers_used, timestamp, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (today, service, quantity, amount, papers_used, timestamp, created_by))
        
        self.db.conn.commit()

class Inventory:
    def __init__(self, db_manager):
        self.db = db_manager
        self.SHEETS_PER_RIM = 500
        self.RIMS_PER_BOX = 5
        self.SHEETS_PER_BOX = self.SHEETS_PER_RIM * self.RIMS_PER_BOX
    
    def add_stock(self, item_type, quantity, unit_type=None):
        """
        Add stock items
        item_type: paper, file, envelope
        unit_type: box, rim (for paper only)
        """
        try:
            current_sheets = self.get_stock(item_type)
            print(f"Current sheets: {current_sheets}")
            
            if item_type == 'paper':
                if unit_type == 'box':
                    sheets_to_add = quantity * (self.SHEETS_PER_RIM * self.RIMS_PER_BOX) 
                    print(f"Adding {quantity} boxes = {sheets_to_add} sheets")
                elif unit_type == 'rim':
                    sheets_to_add = quantity * self.SHEETS_PER_RIM  
                    print(f"Adding {quantity} rims = {sheets_to_add} sheets")
                else:
                    sheets_to_add = quantity
                    print(f"Adding {quantity} direct sheets")
                
         
                new_total_sheets = current_sheets + sheets_to_add
                print(f"New total sheets: {new_total_sheets}")
                
                self.db.cursor.execute('''
                    UPDATE inventory 
                    SET quantity = ?, last_updated = ?
                    WHERE item = ?
                ''', (new_total_sheets, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item_type))
            else:
                new_quantity = current_sheets + quantity
                self.db.cursor.execute('''
                    UPDATE inventory 
                    SET quantity = ?, last_updated = ?
                    WHERE item = ?
                ''', (new_quantity, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item_type))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error adding stock: {e}")
            return False

    def get_stock(self, item_type=None):
        if item_type:
            self.db.cursor.execute('SELECT quantity FROM inventory WHERE item = ?', (item_type,))
            result = self.db.cursor.fetchone()
            return result[0] if result else 0
        else:
            self.db.cursor.execute('SELECT item, quantity FROM inventory')
            stock = {}
            
            for item, quantity in self.db.cursor.fetchall():
                if item == 'paper':
                    total_sheets = quantity
                    
                    boxes = total_sheets // (self.SHEETS_PER_RIM * self.RIMS_PER_BOX)
                    remaining_sheets = total_sheets % (self.SHEETS_PER_RIM * self.RIMS_PER_BOX)
                    rims = remaining_sheets // self.SHEETS_PER_RIM
                    sheets = remaining_sheets % self.SHEETS_PER_RIM
                    
                    stock[item] = {
                        'boxes': boxes,
                        'rims': rims,
                        'sheets': sheets,
                        'total_sheets': total_sheets
                    }
                else:
                    stock[item] = {'quantity': quantity}
                    
            return stock

    def update_stock(self, item_type, quantity_change):
        """Update stock quantity"""
        try:
            current_stock = self.get_stock(item_type)
            new_quantity = current_stock + quantity_change
            
            self.db.cursor.execute('''
                UPDATE inventory 
                SET quantity = ?, last_updated = ?
                WHERE item = ?
            ''', (new_quantity, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item_type))
            
            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating stock: {e}")
            return False
class Expense:
    def __init__(self, db_manager):
        self.db = db_manager

    def add_expense(self, category, amount, description):
        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.db.cursor.execute('''
            INSERT INTO expenses 
            (date, category, amount, description, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (today, category, amount, description, timestamp))
        
        self.db.conn.commit()
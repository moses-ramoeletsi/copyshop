import csv
import os
from datetime import datetime

from models import Expense, Inventory, Transaction
class PrintShopService:
    def __init__(self, db_manager, current_user=None):
        self.db = db_manager
        self.transaction_model = Transaction(db_manager)
        self.inventory_model = Inventory(db_manager)
        self.expense_model = Expense(db_manager)
        self.current_user = current_user
        
        self.prices = {
            "Photocopy": 2.00,
            "Printing": 3.00,
            "Scanning": 4.00,
            "Lamination": 10.00,
            "File": 15.00,
            "Envelope": 3.00
        }
        
        self.stock_thresholds = {
            "paper": 50,
            "file": 20,
            "envelope": 20
        }

    def set_current_user(self, user):
        """Set the current user for the service"""
        self.current_user = user

    def process_transaction(self, service, quantity, papers_per_item=0):
        """Process a new transaction"""
        amount = quantity * self.prices[service]
        total_papers = quantity * papers_per_item if papers_per_item > 0 else 0
        
        if service == "File":
            self.inventory_model.update_stock('file', -quantity)
        elif service == "Envelope":
            self.inventory_model.update_stock('envelope', -quantity)
        
        if total_papers > 0:
            self.inventory_model.update_stock('paper', -total_papers)
        
        username = self.current_user.username if self.current_user else None
        self.transaction_model.add_transaction(service, quantity, amount, total_papers, created_by=username)
        
        return amount, total_papers
    def get_daily_summary(self):
            """Get summary of today's transactions"""
            today = datetime.now().strftime('%Y-%m-%d')
            
            self.db.cursor.execute('''
                SELECT SUM(amount), SUM(papers_used)
                FROM transactions 
                WHERE date = ?
            ''', (today,))
            
            result = self.db.cursor.fetchone()
            total_amount, total_papers = result if result else (0, 0)
            return total_amount or 0, total_papers or 0

    def get_service_summary(self):
        """Get summary of services for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        summary = {}
        
        for service in self.prices.keys():
            self.db.cursor.execute('''
                SELECT COUNT(*), SUM(amount) 
                FROM transactions 
                WHERE date = ? AND service = ?
            ''', (today, service))
            
            count, total = self.db.cursor.fetchone()
            summary[service] = {
                'count': count or 0,
                'amount': total or 0
            }
        
        return summary

    def end_day(self):
        """Process end of day operations"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        self.db.cursor.execute('''
            SELECT category, SUM(amount) 
            FROM expenses 
            WHERE date = ?
            GROUP BY category
        ''', (today,))
        
        expenses_dict = dict(self.db.cursor.fetchall())
        total_expenses = sum(expenses_dict.values())
        
        daily_income, papers_used = self.get_daily_summary()
        balance = daily_income - total_expenses
        
        self.db.cursor.execute('''
            INSERT OR REPLACE INTO daily_records 
            (date, daily_income, mottakase, pampiri, ink_cardrige, drawings, 
             total_expenses, balance, papers_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (today, daily_income,
              expenses_dict.get('Mottakase', 0),
              expenses_dict.get('Pampiri', 0),
              expenses_dict.get('INK/Cardrige', 0),
              expenses_dict.get('Drawings', 0),
              total_expenses, balance,
              papers_used))
        
        self.db.conn.commit()
        
        self.generate_daily_report(today)

    def generate_daily_report(self, date):
        """Generate detailed end of day report"""
        report_dir = "reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        filename = os.path.join(report_dir, f"daily_report_{date}.txt")
        daily_income, papers_used = self.get_daily_summary()
        
        with open(filename, 'w') as f:
            f.write(f"Daily Report - {date}\n")
            f.write("="*50 + "\n\n")
            
            f.write("Revenue Breakdown:\n")
            f.write("-"*20 + "\n")
            
            service_summary = self.get_service_summary()
            for service, data in service_summary.items():
                f.write(f"{service}: {data['count']} transactions - M{data['amount']:.2f}\n")
            
            f.write(f"\nTotal Revenue: M{daily_income:.2f}\n")
            f.write(f"Papers Used: {papers_used}\n\n")
            
            f.write("Expenses Breakdown:\n")
            f.write("-"*20 + "\n")
            
            self.db.cursor.execute('''
                SELECT category, amount, description
                FROM expenses 
                WHERE date = ?
            ''', (date,))
            
            for category, amount, description in self.db.cursor.fetchall():
                f.write(f"{category}: M{amount:.2f} - {description}\n")

    def export_data(self):
        """Export data to CSV files"""
        export_dir = "exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        with open(os.path.join(export_dir, f'transactions_{timestamp}.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Service', 'Quantity', 'Amount', 'Papers Used', 'Timestamp'])
            
            self.db.cursor.execute('''
                SELECT date, service, quantity, amount, papers_used, timestamp 
                FROM transactions
            ''')
            writer.writerows(self.db.cursor.fetchall())
        
        with open(os.path.join(export_dir, f'daily_records_{timestamp}.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Daily Income', 'Mottakase', 'Pampiri', 'INK/Cardrige',
                           'Drawings', 'Total Expenses', 'Balance', 'Papers Used'])
            
            self.db.cursor.execute('SELECT * FROM daily_records')
            writer.writerows(self.db.cursor.fetchall())

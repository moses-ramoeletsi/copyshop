import hashlib
import sqlite3
from datetime import datetime

class User:
    def __init__(self, username, role, full_name):
        self.username = username
        self.role = role
        self.full_name = full_name

class AuthManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.init_auth_database()
        self.create_admin_if_not_exists()
        self.current_user = None

    def init_auth_database(self):
        """Initialize authentication related tables"""
        self.db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT
            )
        ''')
        self.db.conn.commit()

    def create_admin_if_not_exists(self):
        """Create default admin account if it doesn't exist"""
        self.db.cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
        if self.db.cursor.fetchone()[0] == 0:
            self.register_user(
                username="admin",
                password="admin123",
                role="admin",
                full_name="System Administrator",
                created_by="system"
            )

    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, role, full_name, created_by):
        """Register a new user"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            password_hash = self.hash_password(password)
            
            self.db.cursor.execute('''
                INSERT INTO users 
                (username, password_hash, role, full_name, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, role, full_name, timestamp, created_by))
            
            self.db.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate(self, username, password):
        """Authenticate user"""
        password_hash = self.hash_password(password)
        
        self.db.cursor.execute('''
            SELECT username, role, full_name 
            FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        result = self.db.cursor.fetchone()
        if result:
            self.current_user = User(result[0], result[1], result[2])
            return True
        return False

    def get_all_users(self):
        """Get list of all users"""
        self.db.cursor.execute('''
            SELECT username, role, full_name, created_at, created_by 
            FROM users
        ''')
        return self.db.cursor.fetchall()

    def update_user(self, username, new_password=None, role=None, full_name=None):
        """Update user information"""
        try:
            update_fields = []
            values = []
            
            if new_password:
                update_fields.append("password_hash = ?")
                values.append(self.hash_password(new_password))
                
            if role:
                update_fields.append("role = ?")
                values.append(role)
                
            if full_name:
                update_fields.append("full_name = ?")
                values.append(full_name)
                
            if not update_fields:
                return True
                
            values.append(username)
            
            self.db.cursor.execute(f'''
                UPDATE users 
                SET {", ".join(update_fields)}
                WHERE username = ?
            ''', values)
            
            self.db.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def delete_user(self, username):
        """Delete a user"""
        try:
            self.db.cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
            admin_count = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute('SELECT role FROM users WHERE username = ?', (username,))
            user_role = self.db.cursor.fetchone()[0]
            
            if admin_count <= 1 and user_role == 'admin':
                return False
                
            self.db.cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            self.db.conn.commit()
            return True
        except sqlite3.Error:
            return False
        
    def is_admin(self):
        """Check if current user is admin"""
        return self.current_user and self.current_user.role == "admin"

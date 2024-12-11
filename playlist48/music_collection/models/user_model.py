import sqlite3
import hashlib
import os
from typing import Dict, Optional
from music_collection.utils.sql_utils import get_db_connection

class UserModel:
    def __init__(self):
        self.db_path = "users.db"

    def hash_password(self, password: str, salt: bytes = None) -> Dict[str, bytes]:
        """
        Hash a password with a salt.
        
        Args:
            password (str): The plain text password to hash
            salt (bytes, optional): Existing salt to use. If None, generate a new salt.
        
        Returns:
            Dict containing salt and hashed password
        """
        if salt is None:
            # Generate a new salt
            salt = os.urandom(32)  # 32 bytes = 256 bits
        
        # Hash the password with the salt using SHA-256
        # We use PBKDF2-like approach with multiple iterations for added security
        hashed_password = hashlib.pbkdf2_hmac(
            'sha256',  # hash digest algorithm
            password.encode('utf-8'),  # convert password to bytes
            salt,  # provide the salt
            100000  # 100,000 iterations of SHA-256 
        )
        
        return {
            'salt': salt,
            'hashed_password': hashed_password
        }

    def create_account(self, username: str, password: str) -> Dict:
        """
        Create a new user account.
        
        Args:
            username (str): The username for the new account
            password (str): The password for the new account
        
        Returns:
            Dict with account creation details
        """
        # Validate inputs
        if not username or not isinstance(username, str):
            raise ValueError("Invalid username")
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Hash the password
        hashed_data = self.hash_password(password)
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (username, salt, hashed_password) VALUES (?, ?, ?)",
                    (username, hashed_data['salt'], hashed_data['hashed_password'])
                )
                conn.commit()
                
                # Get the newly created user's ID
                user_id = cursor.lastrowid
                
                return {
                    "id": user_id,
                    "username": username,
                    "message": "Account created successfully"
                }
        except sqlite3.IntegrityError:
            raise ValueError("Username already exists")
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            raise ValueError("Failed to create account")

    def login(self, username: str, password: str) -> Dict:
        """
        Authenticate a user.
        
        Args:
            username (str): The username to authenticate
            password (str): The password to verify
        
        Returns:
            Dict with login details if successful
        """
        # Validate inputs
        if not username or not password:
            raise ValueError("Username and password are required")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Retrieve user data
                cursor.execute(
                    "SELECT id, salt, hashed_password FROM users WHERE username = ?",
                    (username,)
                )
                user = cursor.fetchone()
                
                if not user:
                    raise ValueError("Invalid username or password")
                
                user_id, stored_salt, stored_hashed_password = user
                
                # Verify password
                if not self.verify_password(password, stored_salt, stored_hashed_password):
                    raise ValueError("Invalid username or password")
                
                return {
                    "id": user_id,
                    "username": username,
                    "message": "Login successful"
                }
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            raise ValueError("Login failed")

    def update_password(self, username: str, old_password: str, new_password: str) -> Dict:
        """
        Update a user's password.
        
        Args:
            username (str): The username of the account
            old_password (str): The current password
            new_password (str): The new password to set
        
        Returns:
            Dict with password update details
        """
        # Validate new password
        if not new_password or len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters long")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # First, verify the old password
                cursor.execute(
                    "SELECT salt, hashed_password FROM users WHERE username = ?",
                    (username,)
                )
                user = cursor.fetchone()
                
                if not user:
                    raise ValueError("User not found")
                
                stored_salt, stored_hashed_password = user
                
                # Verify old password
                if not self.verify_password(old_password, stored_salt, stored_hashed_password):
                    raise ValueError("Current password is incorrect")
                
                # Hash the new password
                new_hashed_data = self.hash_password(new_password)
                
                # Update password
                cursor.execute(
                    "UPDATE users SET salt = ?, hashed_password = ? WHERE username = ?",
                    (new_hashed_data['salt'], new_hashed_data['hashed_password'], username)
                )
                conn.commit()
                
                return {
                    "username": username,
                    "message": "Password updated successfully"
                }
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            raise ValueError("Failed to update password")

    def verify_password(self, input_password: str, stored_salt: bytes, stored_hashed_password: bytes) -> bool:
        """
        Verify a password against stored salt and hashed password.
        
        Args:
            input_password (str): The password to verify
            stored_salt (bytes): The salt used when the password was originally hashed
            stored_hashed_password (bytes): The original hashed password
        
        Returns:
            bool: True if password is correct, False otherwise
        """
        # Hash the input password with the stored salt
        hashed_data = self.hash_password(input_password, stored_salt)
        
        # Compare the newly hashed password with the stored hashed password
        return hashed_data['hashed_password'] == stored_hashed_password
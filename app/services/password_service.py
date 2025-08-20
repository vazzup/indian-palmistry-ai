"""
Password hashing and verification service using bcrypt.
"""

import bcrypt


class PasswordService:
    """Service for password hashing and verification using bcrypt."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password as string
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Hashed password to check against
            
        Returns:
            True if password matches hash, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            # Invalid hash format or other bcrypt errors
            return False
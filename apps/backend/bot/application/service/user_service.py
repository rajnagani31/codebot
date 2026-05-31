"""
Example service showing how to use the centralized database setup
"""

from typing import Optional, List
from ..core.database import get_db_sync, get_db
from ..core.db_utils import BaseRepository, with_transaction
from ..model.chat_history import ChatUser, UserSession


class UserService:
    """Service for user-related operations"""
    
    def __init__(self):
        self.user_repo = BaseRepository(ChatUser)
        self.session_repo = BaseRepository(UserSession)
    
    def create_user(self, email: str, display_name: str = None, user_type: str = "guest") -> ChatUser:
        """Create a new user"""
        user_data = {
            "email": email,
            "display_name": display_name,
            "user_type": user_type
        }
        return self.user_repo.create(**user_data)
    
    def get_user_by_email(self, email: str) -> Optional[ChatUser]:
        """Get user by email"""
        users = self.user_repo.find_by(email=email)
        return users[0] if users else None
    
    def get_user_by_public_id(self, public_id: str) -> Optional[ChatUser]:
        """Get user by public ID"""
        users = self.user_repo.find_by(public_id=public_id)
        return users[0] if users else None
    
    def update_user_last_seen(self, user_id: int) -> bool:
        """Update user's last seen timestamp"""
        from datetime import datetime
        return self.user_repo.update(user_id, last_seen_at=datetime.utcnow()) is not None
    
    def create_user_session(self, user_id: int, auth_method: str = "guest") -> UserSession:
        """Create a new user session"""
        import secrets
        from datetime import datetime, timedelta
        
        session_data = {
            "user_id": user_id,
            "auth_method": auth_method,
            "session_token_hash": secrets.token_hex(32),
            "refresh_token_hash": secrets.token_hex(32),
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
            "refresh_expires_at": datetime.utcnow() + timedelta(days=30)
        }
        return self.session_repo.create(**session_data)
    
    def search_users(self, search_term: str) -> List[ChatUser]:
        """Search users by display name or email"""
        return self.user_repo.search(search_term, ["display_name", "email"])
    
    def get_active_users_count(self) -> int:
        """Get count of active users"""
        return self.user_repo.count()
    
    @with_transaction
    def create_user_with_session(self, user_data: dict, session_data: dict, db=None):
        """Create user and session in a single transaction"""
        user = BaseRepository(ChatUser, db).create(**user_data)
        session_data["user_id"] = user.id
        session = BaseRepository(UserSession, db).create(**session_data)
        return user, session


# Usage examples:
def example_usage():
    """Examples of how to use the database setup"""
    
    # Method 1: Using service class
    user_service = UserService()
    
    # Create a user
    user = user_service.create_user(
        email="test@example.com",
        display_name="Test User"
    )
    
    # Create a session for the user
    session = user_service.create_user_session(user.id)
    
    # Search for users
    found_users = user_service.search_users("test")
    
    # Method 2: Using repository directly
    from ..core.database import get_db_sync
    db = get_db_sync()
    try:
        user_repo = BaseRepository(ChatUser, db)
        all_users = user_repo.get_all(limit=10)
        user_count = user_repo.count()
    finally:
        db.close()
    
    # Method 3: Using dependency injection (FastAPI style)
    db_gen = get_db()
    db = next(db_gen)
    try:
        user_repo = BaseRepository(ChatUser, db)
        user = user_repo.get_by_id(1)
    finally:
        db.close()

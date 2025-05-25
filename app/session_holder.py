
from flask import session
from flask.sessions import SessionMixin
from app.dao.model.user import User
from app.utils.concurrent_dict import ConcurrentDict
import hashlib, json

class SessionHolder:
    """
    Manages user authentication sessions by maintaining a mapping between session tokens,
    user objects, and session instances.

    This class provides utility methods for establishing, retrieving, and evicting user sessions.
    It also ensures session uniqueness by generating a hashed token for each authenticated user.

    Attributes:
        session_dict (ConcurrentDict[str, User]):
            A thread-safe dictionary mapping session tokens to authenticated User objects.
        token_dict (ConcurrentDict[str, SessionMixin]):
            A thread-safe dictionary mapping session tokens to their respective session instances.
    """


    session_dict: ConcurrentDict[str, User] = ConcurrentDict()
    token_dict: ConcurrentDict[str, SessionMixin] = ConcurrentDict()

    
    @staticmethod
    def session_hold(session: SessionMixin, user: User) -> None:
        """
        Establishes a new session for the given authenticated user by generating a unique session token
        and storing the session details in the internal dictionaries.

        Args:
            session (SessionMixin): The current Flask session instance.
            user (User): The authenticated user object.

        Side Effects:
            - Assigns a generated session token to the Flask session.
            - Maps the generated token to the user and session in internal storage.
        """
        token: str = SessionHolder.generate_token(user)
        SessionHolder.session_dict[token] = user
        SessionHolder.token_dict[token] = session
        session['token'] = token         # Explicit assignment
        session.modified = True          # Force Flask to store the session

    
    @staticmethod
    def session_evict(session: SessionMixin, user: User) -> None:
        """
        Terminates an active session for the given user. If no user is specified,
        it clears the session for the current token.

        Args:
            session (SessionMixin): The current Flask session instance.
            user (User): The user whose session needs to be invalidated. If None, clears the current session.

        Side Effects:
            - Removes the session token from internal storage.
            - Deletes the session token from the Flask session.
        """
        if user == None:
            token: str = session.pop('token', None)
            SessionHolder.session_dict.pop(token, None)
            SessionHolder.token_dict.pop(token, None)
        else:
            token: str = SessionHolder.generate_token(user)
            SessionHolder.session_dict.pop(token, None)
            session: SessionMixin = SessionHolder.token_dict.pop(token, None)
            if session:
                session.pop('token', None)

    
    @staticmethod
    def current_login() -> User:
        """
        Retrieves the currently authenticated user based on the active session token.

        Returns:
            User: The User object corresponding to the active session, or None if no valid session exists.
        """
        return SessionHolder.session_dict.get(session.get('token'), None)
    
    
    @staticmethod
    def session_exists(token: str) -> bool:
        """
        Checks if a session exists for the given session token.

        Args:
            token (str): The session token to validate.
        
        Returns:
            bool: True if a session is active for the given token, False otherwise.
        """
        return session.get('token') != None

    
    @staticmethod
    def generate_token(user: User) -> str:
        """
        Generates a unique, deterministic session token for the given user by hashing their user ID.
        This ensures session consistency across requests while maintaining security.

        Args:
            user (User): The user object for whom the token is being generated.
        
        Returns:
            str: A hashed session token that uniquely represents the user session.
        """
        user_info = json.dumps({"user_id": user.user_id}, sort_keys = True)
        return hashlib.md5(user_info.encode()).hexdigest()
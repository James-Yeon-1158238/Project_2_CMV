

from typing import Callable, List
from functools import wraps

from flask import session
from app.constant.user_role import Role
from app.dao.model.user import User
from app.exception.custom_error import AccessDeclinedError, UnauthorizedError
from app.session_holder import SessionHolder


def token_check(*, options: List[Role]):
    """
    Decorator to enforce role-based access control.

    This decorator checks whether the current user is authenticated and 
    possesses the required role(s) before allowing access to the decorated function.

    Args:
        options (List[Role]): A list of allowed roles for accessing the decorated function.

    Raises:
        AccessDeclinedError: If the user is not logged in, session has expired, 
                             or the user's role is not in the allowed roles.

    Returns:
        Callable: The wrapped function with access control enforced.

    Example:
        ```python
        @token_check(options=[Role.ADMIN])
        def admin_dashboard():
            return "Welcome to the admin panel"
        ```
    """
    def decorator(func):
        # Preserve the original function's metadata
        @wraps(func)
        def wrapper(*args, **kwargs):
            token: str = session.get('token', None)
            # Check if the token is absent
            if token is None:
                raise UnauthorizedError('no login information')
            # Check if the session is still valid
            current_login: User = SessionHolder.current_login()
            if not current_login:
                SessionHolder.session_evict(session, None)
                raise UnauthorizedError('login information expires')
            # If no role restrictions are provided, allow access
            if options is None or len(options) == 0:
                return func(*args, **kwargs)
            # Check if the user’s role is in the allowed options
            if current_login.get_role_enum() not in options:
                raise AccessDeclinedError('this operation is not allowed')
            # If all checks pass, call the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator


def current_user(*, id_func: Callable[[], str]):
    """
    Decorator to ensure that a user can only access their own resources.

    This decorator retrieves the current user's session and verifies that
    the user ID matches the expected ID provided by `id_func`.

    Args:
        id_func (Callable[[], str]): A function that returns the expected user ID.

    Raises:
        AccessDeclinedError: If the user is not logged in or is trying to access 
                             another user's data.

    Returns:
        Callable: The wrapped function with user ownership validation.

    Example:
        ```python
        @current_user(id_func=lambda: request.form.get('user_id'))
        def update_profile():
            return "Profile updated"
        ```
    """
    def decorator(func):
        # Preserve the original function's metadata
        @wraps(func)
        def wrapper(*args, **kwargs):
            token: str = session.get('token', None)
            # Check if the token is absent
            if token is None:
                raise UnauthorizedError('no login information found')
            # Retrieve the currently logged-in user from the session
            current_login: User = SessionHolder.current_login()
            if not current_login:
                SessionHolder.session_evict(session, None)
                raise UnauthorizedError('login information expires')
            # Check if the current user's ID matches the expected ID
            if str(current_login.user_id) != id_func():
                raise AccessDeclinedError('this operation is not allowed')
            # If all checks pass, execute the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator
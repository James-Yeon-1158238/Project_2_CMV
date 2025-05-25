from flask import Flask, Response, jsonify
from app.exception.custom_error import *


def init_error_handlers(app: Flask) -> None:
    """
    Registers custom error handlers for the Flask application.

    This function binds specific exception classes to HTTP responses, ensuring that meaningful
    error messages are returned to clients when exceptions occur during request handling.

    Args:
        app (Flask): The Flask application instance to which the error handlers will be attached.

    Handled Exceptions:
        - ArgumentError (400 Bad Request): Raised when invalid arguments are provided in a request.
        - UnauthorizedError (401 Unauthorized): Raised when authentication fails due to missing or invalid credentials.
        - NotFoundError (404 Not Found): Raised when a requested resource cannot be located.
        - AccessDeclinedError (403 Forbidden): Raised when a user attempts an action they are not authorized to perform.
        - Exception (500 Internal Server Error): Catches any unhandled exceptions and returns a generic error response.

    Returns:
        None: This function does not return a value, but it modifies the Flask application instance.
    """

    
    @app.errorhandler(ArgumentError)
    def argument_error_handler(error: ArgumentError) -> Response:
        """
        Handles ArgumentError exceptions and returns an appropriate HTTP 400 response.

        This exception is typically raised when a request contains missing, malformed,
        or invalid parameters.

        Args:
            error (ArgumentError): The exception instance containing error details.

        Returns:
            Response: A JSON response with an error message and HTTP status 400 (Bad Request).
        """
        return jsonify({
            "err": error.get_error_args()
        }), 400
    
    
    @app.errorhandler(UnauthorizedError)
    def unauthorized_error_handler(error: UnauthorizedError) -> Response:
        """
        Handles UnauthorizedError exceptions and returns an HTTP 401 response.

        This exception is raised when a user attempts to access a protected resource
        without valid authentication.

        Args:
            error (UnauthorizedError): The exception instance containing error details.

        Returns:
            Response: A JSON response with an error message and HTTP status 401 (Unauthorized).
        """
        return jsonify({
            "err": error.message
        }), 401
    
    
    @app.errorhandler(AccessDeclinedError)
    def declined_error_handler(error: AccessDeclinedError) -> Response:
        """
        Handles AccessDeclinedError exceptions and returns an HTTP 403 response.

        This exception is raised when a user attempts to access a resource or perform
        an action that they are not authorized to.

        Args:
            error (AccessDeclinedError): The exception instance containing error details.

        Returns:
            Response: A JSON response with an error message and HTTP status 403 (Forbidden).
        """
        return jsonify({
            "err": error.message
        }), 403
    

    @app.errorhandler(OperationNotAllowedError)
    def operation_not_allowed_handler(error: OperationNotAllowedError) -> Response:
        return jsonify({
            "err": error.message
        }), 405
    
    
    @app.errorhandler(Exception)
    def unknown_error_handler(error: Exception) -> Response:
        """
        Handles all unexpected exceptions and returns an HTTP 500 response.

        This function catches all unhandled exceptions, logs the error, and provides a
        generic error response to prevent exposing sensitive information.

        Args:
            error (Exception): The unhandled exception instance.

        Returns:
            Response: A JSON response with a generic error message and HTTP status 500 (Internal Server Error).
        """
        print(error)
        return jsonify({
            "err": "service unavilable"
        }), 500
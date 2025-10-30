"""
Authentication Helper - Validates AUTH_TOKEN for inter-module calls
"""

from flask import request, jsonify
from core.config_manager import get_auth_token

def require_auth_token(func):
    """Decorator to require AUTH token for endpoint"""
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        expected_token = get_auth_token()
        
        if not expected_token:
            # No token configured, allow access (development mode)
            return func(*args, **kwargs)
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                "error": "Missing or invalid Authorization header",
                "message": "Authorization: Bearer <token> required"
            }), 401
        
        token = auth_header.replace('Bearer ', '').strip()
        if token != expected_token:
            return jsonify({
                "error": "Invalid authentication token"
            }), 401
        
        return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    return wrapper





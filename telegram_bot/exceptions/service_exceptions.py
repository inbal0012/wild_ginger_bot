class ServiceException(Exception):
    """Base exception for service errors"""
    pass

class RegistrationNotFoundException(ServiceException):
    """Raised when registration is not found"""
    pass

class SheetsConnectionException(ServiceException):
    """Raised when Google Sheets connection fails"""
    pass

class UnauthorizedOperationException(ServiceException):
    """Raised when user lacks permissions"""
    pass

class InvalidDataException(ServiceException):
    """Raised when data validation fails"""
    pass

class ConversationStateException(ServiceException):
    """Raised when conversation state is invalid"""
    pass 
"""
Advanced Error Handling and Recovery System
Error Classification and Retry Logic
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import traceback

class ErrorCategory(Enum):
    """Categories of errors for different handling strategies"""
    TRANSIENT = "transient"          # Network timeouts, API limits
    RECOVERABLE = "recoverable"      # Input format, missing dependencies
    FATAL = "fatal"                  # Auth failures, system crashes
    UNKNOWN = "unknown"              # Unclassified errors

class ErrorSeverity(Enum):
    """Severity levels for error prioritization"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    suggested_fix: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'error_type': self.error_type,
            'error_message': self.error_message,
            'category': self.category.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp,
            'context': self.context,
            'stack_trace': self.stack_trace,
            'suggested_fix': self.suggested_fix,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

class ErrorClassifier:
    """Classifies errors based on patterns and rules"""
    
    def __init__(self):
        self.classification_rules = {
            # Transient errors - auto-retry
            ErrorCategory.TRANSIENT: [
                "timeout", "connection", "network", "rate limit", "429", 
                "502", "503", "504", "temporary", "unavailable"
            ],
            
            # Recoverable errors - retry with adjustment
            ErrorCategory.RECOVERABLE: [
                "invalid format", "missing file", "permission", "format error",
                "validation", "input error", "resource busy", "lock"
            ],
            
            # Fatal errors - no retry
            ErrorCategory.FATAL: [
                "authentication", "authorization", "401", "403", "security",
                "system crash", "memory", "disk full", "critical"
            ]
        }
        
        self.severity_rules = {
            ErrorSeverity.CRITICAL: ["crash", "fatal", "system", "security"],
            ErrorSeverity.HIGH: ["failure", "error", "exception", "failed"],
            ErrorSeverity.MEDIUM: ["warning", "invalid", "missing"],
            ErrorSeverity.LOW: ["info", "debug", "notice"]
        }
    
    def classify_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Classify an error and return ErrorInfo"""
        error_message = str(error)
        error_type = type(error).__name__
        
        category = self._determine_category(error_message, error_type)
        severity = self._determine_severity(error_message, error_type)
        
        return ErrorInfo(
            error_type=error_type,
            error_message=error_message,
            category=category,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            context=context or {},
            stack_trace=traceback.format_exc(),
            suggested_fix=self._suggest_fix(category, error_type, error_message),
            max_retries=self._get_max_retries(category)
        )
    
    def _determine_category(self, message: str, error_type: str) -> ErrorCategory:
        """Determine error category based on message and type"""
        message_lower = message.lower()
        type_lower = error_type.lower()
        
        for category, keywords in self.classification_rules.items():
            if any(keyword in message_lower or keyword in type_lower for keyword in keywords):
                return category
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, message: str, error_type: str) -> ErrorSeverity:
        """Determine error severity"""
        message_lower = message.lower()
        type_lower = error_type.lower()
        
        for severity, keywords in self.severity_rules.items():
            if any(keyword in message_lower or keyword in type_lower for keyword in keywords):
                return severity
        
        return ErrorSeverity.MEDIUM
    
    def _suggest_fix(self, category: ErrorCategory, error_type: str, message: str) -> Optional[str]:
        """Suggest a fix based on error category and type"""
        suggestions = {
            ErrorCategory.TRANSIENT: "Wait and retry with exponential backoff",
            ErrorCategory.RECOVERABLE: "Check input format and dependencies, then retry",
            ErrorCategory.FATAL: "Manual intervention required - check logs and configuration",
            ErrorCategory.UNKNOWN: "Investigate error pattern and add classification rule"
        }
        
        return suggestions.get(category)
    
    def _get_max_retries(self, category: ErrorCategory) -> int:
        """Get maximum retry attempts for error category"""
        retry_limits = {
            ErrorCategory.TRANSIENT: 3,
            ErrorCategory.RECOVERABLE: 2,
            ErrorCategory.FATAL: 0,
            ErrorCategory.UNKNOWN: 1
        }
        
        return retry_limits.get(category, 1)

class RetryManager:
    """Manages retry logic with exponential backoff and circuit breaker"""
    
    def __init__(self):
        self.retry_history: Dict[str, List[float]] = {}
        self.circuit_breakers: Dict[str, bool] = {}
        self.classifier = ErrorClassifier()
        
        # Configuration
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 30.0  # Maximum delay in seconds
        self.circuit_breaker_threshold = 5  # Failures before circuit opens
        self.circuit_breaker_timeout = 300  # 5 minutes
    
    def should_retry(self, error: Exception, context: Dict[str, Any] = None) -> Tuple[bool, ErrorInfo]:
        """Determine if an error should be retried"""
        error_info = self.classifier.classify_error(error, context)
        
        # Check circuit breaker
        if self._is_circuit_open(error_info.error_type):
            return False, error_info
        
        # Check retry count
        if error_info.retry_count >= error_info.max_retries:
            return False, error_info
        
        # Check if error category allows retries
        if error_info.category == ErrorCategory.FATAL:
            return False, error_info
        
        return True, error_info
    
    def calculate_delay(self, error_info: ErrorInfo) -> float:
        """Calculate delay before retry using exponential backoff"""
        if error_info.category == ErrorCategory.TRANSIENT:
            # Exponential backoff: delay = base_delay * (2 ^ retry_count)
            delay = self.base_delay * (2 ** error_info.retry_count)
        else:
            # Linear backoff for recoverable errors
            delay = self.base_delay * (error_info.retry_count + 1)
        
        return min(delay, self.max_delay)
    
    def record_failure(self, error_info: ErrorInfo):
        """Record a failure for circuit breaker logic"""
        error_type = error_info.error_type
        current_time = time.time()
        
        if error_type not in self.retry_history:
            self.retry_history[error_type] = []
        
        self.retry_history[error_type].append(current_time)
        
        # Check if circuit breaker should open
        recent_failures = [
            t for t in self.retry_history[error_type]
            if current_time - t < self.circuit_breaker_timeout
        ]
        
        if len(recent_failures) >= self.circuit_breaker_threshold:
            self.circuit_breakers[error_type] = True
            logging.warning(f"Circuit breaker opened for {error_type}")
    
    def _is_circuit_open(self, error_type: str) -> bool:
        """Check if circuit breaker is open for this error type"""
        return self.circuit_breakers.get(error_type, False)
    
    def reset_circuit_breaker(self, error_type: str):
        """Manually reset circuit breaker"""
        self.circuit_breakers[error_type] = False
        logging.info(f"Circuit breaker reset for {error_type}")

class RecoveryStrategy:
    """Implements recovery strategies for different error types"""
    
    def __init__(self):
        self.strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.TRANSIENT: self._handle_transient_error,
            ErrorCategory.RECOVERABLE: self._handle_recoverable_error,
            ErrorCategory.FATAL: self._handle_fatal_error,
            ErrorCategory.UNKNOWN: self._handle_unknown_error
        }
    
    def apply_recovery(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply appropriate recovery strategy"""
        strategy = self.strategies.get(error_info.category, self._handle_unknown_error)
        return strategy(error_info, context)
    
    def _handle_transient_error(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transient errors with retry logic"""
        return {
            "action": "retry",
            "delay": RetryManager().calculate_delay(error_info),
            "modifications": {},
            "message": f"Retrying after {error_info.retry_count} attempts"
        }
    
    def _handle_recoverable_error(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle recoverable errors with context adjustment"""
        modifications = {}
        
        # Common recovery modifications
        if "format" in error_info.error_message.lower():
            modifications["data_format"] = "json"
        
        if "missing" in error_info.error_message.lower():
            modifications["create_if_missing"] = True
        
        return {
            "action": "retry_with_modification",
            "delay": 2.0,  # Short delay for recoverable errors
            "modifications": modifications,
            "message": f"Attempting recovery with modifications: {modifications}"
        }
    
    def _handle_fatal_error(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fatal errors - no automatic recovery"""
        return {
            "action": "escalate",
            "delay": 0,
            "modifications": {},
            "message": f"Fatal error requires manual intervention: {error_info.error_message}"
        }
    
    def _handle_unknown_error(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown errors with conservative approach"""
        return {
            "action": "investigate",
            "delay": 5.0,
            "modifications": {},
            "message": f"Unknown error pattern - investigate: {error_info.error_message}"
        }

# Global instances
error_classifier = ErrorClassifier()
retry_manager = RetryManager()
recovery_strategy = RecoveryStrategy()

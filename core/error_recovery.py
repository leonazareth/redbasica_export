"""
Error recovery and graceful degradation system for the Flexible Sewerage DXF Export Plugin.

This module provides mechanisms for graceful error recovery, feature skipping,
and detailed progress reporting during export operations.
"""

import traceback
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from qgis.core import QgsFeature, QgsMessageLog, Qgis
    QGIS_AVAILABLE = True
except ImportError:
    # Mock QGIS classes for testing
    class QgsFeature:
        def __init__(self):
            pass
        def id(self):
            return 1
        def attributes(self):
            return []
        def geometry(self):
            return None
    
    class QgsMessageLog:
        @staticmethod
        def logMessage(message, tag, level):
            print(f"[{tag}] {message}")
    
    class Qgis:
        Info = "Info"
        Warning = "Warning"
        Critical = "Critical"
        
        class MessageLevel:
            Info = "Info"
            Warning = "Warning"
            Critical = "Critical"
    
    QGIS_AVAILABLE = False

try:
    from .exceptions import (
        ValidationError, LayerValidationError, MappingValidationError,
        ExportError, GeometryError
    )
except ImportError:
    from exceptions import (
        ValidationError, LayerValidationError, MappingValidationError,
        ExportError, GeometryError
    )


class ErrorSeverity(Enum):
    """Error severity levels for recovery decisions."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Record of an error that occurred during processing."""
    severity: ErrorSeverity
    message: str
    feature_id: Optional[str] = None
    layer_name: Optional[str] = None
    error_type: str = "general"
    exception: Optional[Exception] = None
    timestamp: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if not self.timestamp:
            import datetime
            self.timestamp = datetime.datetime.now().isoformat()
    
    def get_display_message(self) -> str:
        """Get formatted message for display to user."""
        parts = []
        
        if self.layer_name:
            parts.append(f"Layer '{self.layer_name}'")
        
        if self.feature_id:
            parts.append(f"Feature {self.feature_id}")
        
        location = " - ".join(parts)
        if location:
            return f"{location}: {self.message}"
        
        return self.message


@dataclass
class ProcessingStats:
    """Statistics for processing operations."""
    total_features: int = 0
    processed_features: int = 0
    skipped_features: int = 0
    failed_features: int = 0
    warnings: int = 0
    errors: int = 0
    
    def get_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_features == 0:
            return 100.0
        return (self.processed_features / self.total_features) * 100.0
    
    def get_summary(self) -> str:
        """Get summary string of processing statistics."""
        return (f"Processed: {self.processed_features}/{self.total_features} "
                f"({self.get_success_rate():.1f}%), "
                f"Skipped: {self.skipped_features}, "
                f"Failed: {self.failed_features}, "
                f"Warnings: {self.warnings}, "
                f"Errors: {self.errors}")


class ErrorRecoveryManager:
    """Manages error recovery strategies and graceful degradation."""
    
    def __init__(self, max_errors: int = 100, max_warnings: int = 500):
        """
        Initialize error recovery manager.
        
        Args:
            max_errors: Maximum number of errors before stopping
            max_warnings: Maximum number of warnings before stopping
        """
        self.max_errors = max_errors
        self.max_warnings = max_warnings
        self.error_records: List[ErrorRecord] = []
        self.stats = ProcessingStats()
        self.recovery_strategies: Dict[str, Callable] = {}
        self.should_continue = True
        
        # Set up default recovery strategies
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Set up default error recovery strategies."""
        self.recovery_strategies = {
            'geometry_error': self._skip_feature_strategy,
            'data_conversion_error': self._use_default_value_strategy,
            'field_missing_error': self._use_default_value_strategy,
            'validation_error': self._skip_feature_strategy,
            'export_error': self._retry_strategy,
        }
    
    def record_error(self, severity: ErrorSeverity, message: str, 
                    feature_id: Optional[str] = None, layer_name: Optional[str] = None,
                    error_type: str = "general", exception: Optional[Exception] = None,
                    context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record an error and determine if processing should continue.
        
        Args:
            severity: Error severity level
            message: Error message
            feature_id: ID of affected feature (if applicable)
            layer_name: Name of affected layer (if applicable)
            error_type: Type of error for recovery strategy selection
            exception: Original exception (if any)
            context: Additional context information
            
        Returns:
            True if processing should continue, False if it should stop
        """
        # Create error record
        error_record = ErrorRecord(
            severity=severity,
            message=message,
            feature_id=feature_id,
            layer_name=layer_name,
            error_type=error_type,
            exception=exception,
            context=context or {}
        )
        
        self.error_records.append(error_record)
        
        # Update statistics
        if severity == ErrorSeverity.WARNING:
            self.stats.warnings += 1
        elif severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self.stats.errors += 1
        
        # Log to QGIS message log
        qgis_level = self._get_qgis_log_level(severity)
        QgsMessageLog.logMessage(
            error_record.get_display_message(),
            "RedBasica Export",
            qgis_level
        )
        
        # Check if we should continue processing
        if severity == ErrorSeverity.CRITICAL:
            self.should_continue = False
            return False
        
        if self.stats.errors >= self.max_errors:
            self.should_continue = False
            self.record_error(
                ErrorSeverity.CRITICAL,
                f"Maximum error limit reached ({self.max_errors}). Stopping processing.",
                error_type="limit_exceeded"
            )
            return False
        
        if self.stats.warnings >= self.max_warnings:
            self.should_continue = False
            self.record_error(
                ErrorSeverity.CRITICAL,
                f"Maximum warning limit reached ({self.max_warnings}). Stopping processing.",
                error_type="limit_exceeded"
            )
            return False
        
        return True
    
    def _get_qgis_log_level(self, severity: ErrorSeverity):
        """Convert error severity to QGIS message level."""
        mapping = {
            ErrorSeverity.INFO: Qgis.Info,
            ErrorSeverity.WARNING: Qgis.Warning,
            ErrorSeverity.ERROR: Qgis.Critical,
            ErrorSeverity.CRITICAL: Qgis.Critical
        }
        return mapping.get(severity, Qgis.Warning)
    
    def apply_recovery_strategy(self, error_type: str, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Apply recovery strategy for a specific error type.
        
        Args:
            error_type: Type of error
            context: Context information for recovery
            
        Returns:
            Tuple of (recovery_successful, recovery_result)
        """
        strategy = self.recovery_strategies.get(error_type, self._skip_feature_strategy)
        
        try:
            return strategy(context)
        except Exception as e:
            self.record_error(
                ErrorSeverity.ERROR,
                f"Recovery strategy failed: {e}",
                error_type="recovery_failure",
                exception=e,
                context=context
            )
            return False, None
    
    def _skip_feature_strategy(self, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """Recovery strategy: skip the problematic feature."""
        feature_id = context.get('feature_id', 'unknown')
        self.stats.skipped_features += 1
        
        self.record_error(
            ErrorSeverity.WARNING,
            f"Skipping feature due to error",
            feature_id=feature_id,
            error_type="feature_skipped"
        )
        
        return True, None
    
    def _use_default_value_strategy(self, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """Recovery strategy: use default value for missing/invalid data."""
        field_name = context.get('field_name', 'unknown')
        default_value = context.get('default_value', '')
        
        self.record_error(
            ErrorSeverity.WARNING,
            f"Using default value '{default_value}' for field '{field_name}'",
            feature_id=context.get('feature_id'),
            error_type="default_value_used"
        )
        
        return True, default_value
    
    def _retry_strategy(self, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """Recovery strategy: retry the operation once."""
        retry_count = context.get('retry_count', 0)
        max_retries = context.get('max_retries', 1)
        
        if retry_count < max_retries:
            context['retry_count'] = retry_count + 1
            return True, context
        else:
            self.record_error(
                ErrorSeverity.ERROR,
                f"Operation failed after {max_retries} retries",
                feature_id=context.get('feature_id'),
                error_type="retry_exhausted"
            )
            return False, None
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors and statistics."""
        error_by_type = {}
        error_by_severity = {}
        
        for record in self.error_records:
            # Count by type
            error_by_type[record.error_type] = error_by_type.get(record.error_type, 0) + 1
            
            # Count by severity
            severity_key = record.severity.value
            error_by_severity[severity_key] = error_by_severity.get(severity_key, 0) + 1
        
        return {
            'statistics': self.stats,
            'total_errors': len(self.error_records),
            'by_type': error_by_type,
            'by_severity': error_by_severity,
            'should_continue': self.should_continue,
            'recent_errors': [r.get_display_message() for r in self.error_records[-10:]]
        }
    
    def get_user_report(self) -> str:
        """Generate user-friendly error report."""
        if not self.error_records:
            return "No errors or warnings occurred during processing."
        
        summary = self.get_error_summary()
        
        report_lines = [
            "Processing Summary:",
            f"- {summary['statistics'].get_summary()}",
            ""
        ]
        
        if summary['by_severity']:
            report_lines.append("Issues by severity:")
            for severity, count in summary['by_severity'].items():
                report_lines.append(f"- {severity.title()}: {count}")
            report_lines.append("")
        
        if summary['by_type']:
            report_lines.append("Issues by type:")
            for error_type, count in summary['by_type'].items():
                report_lines.append(f"- {error_type.replace('_', ' ').title()}: {count}")
            report_lines.append("")
        
        if summary['recent_errors']:
            report_lines.append("Recent issues:")
            for error_msg in summary['recent_errors']:
                report_lines.append(f"- {error_msg}")
        
        return "\n".join(report_lines)


class ProgressTracker:
    """Tracks and reports progress during export operations."""
    
    def __init__(self, total_steps: int, callback: Optional[Callable] = None):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps in the operation
            callback: Optional callback function for progress updates
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.callback = callback
        self.step_messages: List[str] = []
        self.start_time = None
        self.step_times: List[float] = []
    
    def start(self):
        """Start progress tracking."""
        import time
        self.start_time = time.time()
        self.update(0, "Starting export process...")
    
    def update(self, step: int, message: str = ""):
        """
        Update progress with current step and message.
        
        Args:
            step: Current step number
            message: Progress message
        """
        import time
        
        self.current_step = step
        
        if message:
            self.step_messages.append(f"Step {step}/{self.total_steps}: {message}")
            
        # Record timing
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.step_times.append(elapsed)
        
        # Call progress callback if provided
        if self.callback:
            progress_percent = int((step / self.total_steps) * 100)
            self.callback(progress_percent, message)
        
        # Log progress to QGIS
        QgsMessageLog.logMessage(
            f"Export Progress: {step}/{self.total_steps} - {message}",
            "RedBasica Export",
            Qgis.Info
        )
    
    def finish(self, success: bool = True, final_message: str = ""):
        """
        Finish progress tracking.
        
        Args:
            success: Whether the operation completed successfully
            final_message: Final status message
        """
        import time
        
        if not final_message:
            final_message = "Export completed successfully" if success else "Export completed with errors"
        
        self.update(self.total_steps, final_message)
        
        # Calculate total time
        if self.start_time:
            total_time = time.time() - self.start_time
            time_message = f"Total time: {total_time:.1f} seconds"
            
            if self.callback:
                self.callback(100, f"{final_message} ({time_message})")
            
            QgsMessageLog.logMessage(
                f"Export finished: {final_message} - {time_message}",
                "RedBasica Export",
                Qgis.Info if success else Qgis.Warning
            )
    
    def get_progress_percentage(self) -> int:
        """Get current progress as percentage."""
        return int((self.current_step / self.total_steps) * 100)
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """Estimate time remaining based on current progress."""
        if not self.step_times or self.current_step == 0:
            return None
        
        avg_time_per_step = sum(self.step_times) / len(self.step_times)
        remaining_steps = self.total_steps - self.current_step
        
        return avg_time_per_step * remaining_steps


def create_error_recovery_context(feature: QgsFeature, layer_name: str, 
                                operation: str) -> Dict[str, Any]:
    """
    Create error recovery context for a feature processing operation.
    
    Args:
        feature: QGIS feature being processed
        layer_name: Name of the layer
        operation: Type of operation being performed
        
    Returns:
        Context dictionary for error recovery
    """
    return {
        'feature_id': str(feature.id()),
        'layer_name': layer_name,
        'operation': operation,
        'feature_attributes': {field.name(): feature[field.name()] for field in feature.fields()} if feature else {},
        'geometry_type': feature.geometry().type() if feature and feature.geometry() else None
    }


def handle_feature_processing_error(error_manager: ErrorRecoveryManager,
                                  exception: Exception, context: Dict[str, Any]) -> bool:
    """
    Handle errors that occur during feature processing.
    
    Args:
        error_manager: Error recovery manager
        exception: Exception that occurred
        context: Processing context
        
    Returns:
        True if processing should continue, False if it should stop
    """
    # Determine error type and severity based on exception
    if isinstance(exception, GeometryError):
        error_type = "geometry_error"
        severity = ErrorSeverity.WARNING
    elif isinstance(exception, (ValidationError, MappingValidationError)):
        error_type = "validation_error"
        severity = ErrorSeverity.WARNING
    elif isinstance(exception, ExportError):
        error_type = "export_error"
        severity = ErrorSeverity.ERROR
    else:
        error_type = "unknown_error"
        severity = ErrorSeverity.ERROR
    
    # Record the error
    continue_processing = error_manager.record_error(
        severity=severity,
        message=str(exception),
        feature_id=context.get('feature_id'),
        layer_name=context.get('layer_name'),
        error_type=error_type,
        exception=exception,
        context=context
    )
    
    # Apply recovery strategy if processing should continue
    if continue_processing:
        recovery_success, recovery_result = error_manager.apply_recovery_strategy(
            error_type, context
        )
        
        if not recovery_success:
            # Recovery failed, record additional error
            error_manager.record_error(
                ErrorSeverity.ERROR,
                f"Recovery strategy failed for {error_type}",
                feature_id=context.get('feature_id'),
                layer_name=context.get('layer_name'),
                error_type="recovery_failure"
            )
            return False
    
    return continue_processing
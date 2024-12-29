from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class PriceUpdate:
    """Structured price update data with validation
    
    Contains both raw price data and validation results to ensure
    data quality and track potential issues.
    """
    token_mint: str
    price: float
    timestamp: datetime
    raw_data: Dict
    is_valid: bool = True
    validation_errors: Optional[List[str]] = None
    
    def __post_init__(self):
        """Ensure validation_errors is a list"""
        if self.validation_errors is None:
            self.validation_errors = []
            
    def add_error(self, error: str) -> None:
        """Add validation error and mark update as invalid
        
        Args:
            error: Error message to add
        """
        if self.validation_errors is None:
            self.validation_errors = []
        self.validation_errors.append(error)
        self.is_valid = False
        
    @property
    def has_errors(self) -> bool:
        """Check if update has any validation errors"""
        return len(self.validation_errors or []) > 0
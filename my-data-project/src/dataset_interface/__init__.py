"""Dataset Interface Module

This module provides a common interface for different datasets,
allowing easy switching between datasets while maintaining the same pipeline.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd


class BaseDatasetInterface(ABC):
    """Base interface for all dataset implementations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize dataset with optional configuration."""
        self.config_path = config_path
        self.config = self._load_config() if config_path else self._get_default_config()
        self.raw_dir = Path(self.config['data']['raw_dir'])
        self.interim_dir = Path(self.config['data']['interim_dir'])
        self.processed_dir = Path(self.config['data']['processed_dir'])
        
    @abstractmethod
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration for this dataset."""
        pass
    
    @abstractmethod
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        pass
        
    @abstractmethod
    def get_table_mapping(self) -> Dict[str, str]:
        """Return mapping of logical table names to actual file names."""
        pass
        
    @abstractmethod
    def clean_data(self) -> Dict[str, pd.DataFrame]:
        """Clean raw data and return processed DataFrames."""
        pass
        
    @abstractmethod
    def validate_data(self) -> bool:
        """Validate data integrity and return True if valid."""
        pass
        
    def create_directories(self):
        """Create necessary directories."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.interim_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    def save_parquet(self, df: pd.DataFrame, name: str, directory: str = 'processed'):
        """Save DataFrame as Parquet file."""
        if directory == 'processed':
            output_dir = self.processed_dir
        elif directory == 'interim':
            output_dir = self.interim_dir
        else:
            output_dir = Path(directory)
            
        output_path = output_dir / f"{name}.parquet"
        df.to_parquet(
            output_path,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        return output_path

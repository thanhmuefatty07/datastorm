"""
Example Dataset Implementation

This is a template showing how to implement a new dataset using the BaseDatasetInterface.
This demonstrates how easy it is to switch to different datasets while maintaining
the same pipeline and output format.
"""

import pandas as pd
import yaml
from pathlib import Path
import logging
from typing import Dict, Any, Optional

# Import the base interface
import sys
sys.path.append(str(Path(__file__).parent.parent))
from dataset_interface import BaseDatasetInterface

logger = logging.getLogger(__name__)


class ExampleDataset(BaseDatasetInterface):
    """
    Example dataset implementation.
    
    This template shows how to implement a new dataset. Simply:
    1. Copy this file to a new directory (e.g., dataset_your_data)
    2. Modify the methods below for your specific data format
    3. Create a corresponding config YAML file
    4. Use with the modular scripts!
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize example dataset."""
        super().__init__(config_path)
        logger.info(f"Initialized ExampleDataset with config: {config_path}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration for this dataset."""
        return {
            'data': {
                'raw_dir': 'data/raw/ExampleDataset',
                'interim_dir': 'data/interim',
                'processed_dir': 'data/processed'
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_table_mapping(self) -> Dict[str, str]:
        """
        Return mapping of logical table names to actual file names.
        
        Modify this to match your dataset's file structure.
        """
        return {
            'main_data': 'main_data.csv',
            'metadata': 'metadata.csv',
            'lookup_table': 'lookup.csv'
        }
    
    def clean_data(self) -> Dict[str, pd.DataFrame]:
        """
        Clean all data and return processed DataFrames.
        
        This is where you implement your dataset-specific cleaning logic.
        The output format should be consistent: Dict[str, pd.DataFrame]
        """
        logger.info("Starting example dataset cleaning...")
        
        table_mapping = self.get_table_mapping()
        cleaned_data = {}
        
        # Example cleaning for each table
        for table_name, file_name in table_mapping.items():
            file_path = self.raw_dir / file_name
            
            if file_path.exists():
                # Load data
                df = pd.read_csv(file_path)
                
                # Apply generic cleaning (customize this)
                df_cleaned = self._clean_table(df, table_name)
                
                cleaned_data[table_name] = df_cleaned
                logger.info(f"Cleaned {table_name}: {df_cleaned.shape[0]:,} rows")
            else:
                logger.warning(f"File not found: {file_path}")
        
        return cleaned_data
    
    def _clean_table(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Apply generic cleaning to a table.
        
        Customize this method based on your data's needs.
        """
        # Example generic cleaning steps
        original_rows = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values (example strategy)
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        df[categorical_cols] = df[categorical_cols].fillna('Unknown')
        
        # Add processed timestamp
        df['processed_at'] = pd.Timestamp.now()
        
        logger.info(f"{table_name}: {original_rows} -> {len(df)} rows after cleaning")
        return df
    
    def validate_data(self) -> bool:
        """
        Validate data integrity.
        
        Customize validation rules based on your dataset.
        """
        logger.info("Validating example dataset...")
        
        try:
            # Check if required files exist
            table_mapping = self.get_table_mapping()
            
            for table_name, file_name in table_mapping.items():
                file_path = self.raw_dir / file_name
                if not file_path.exists():
                    logger.error(f"Missing required file: {file_name}")
                    return False
                
                # Check if file is readable
                try:
                    df = pd.read_csv(file_path, nrows=1)
                    if df.empty:
                        logger.error(f"File is empty: {file_name}")
                        return False
                except Exception as e:
                    logger.error(f"Cannot read file {file_name}: {e}")
                    return False
            
            logger.info("✓ Data validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False
    
    def process_all(self):
        """Run full cleaning pipeline and save results."""
        if not self.validate_data():
            raise ValueError("Data validation failed - cannot proceed")
        
        # Clean all data
        all_data = self.clean_data()
        
        # Save all cleaned datasets
        for name, df in all_data.items():
            self.save_parquet(df, name)
            logger.info(f"Saved {name}.parquet ({df.shape[0]:,} rows)")
        
        logger.info("Example dataset processing completed!")


# Factory function
def create_dataset(config_path: Optional[str] = None) -> ExampleDataset:
    """Factory function to create ExampleDataset instance."""
    return ExampleDataset(config_path)


# Usage example:
if __name__ == "__main__":
    # This shows how to use the dataset directly
    
    # Create dataset (will use default config if none provided)
    dataset = create_dataset()
    
    # Or with custom config:
    # dataset = create_dataset("configs/dataset_example_paths.yaml")
    
    # Validate first
    if dataset.validate_data():
        print("✓ Data is valid")
        
        # Process all data
        dataset.process_all()
        print("✓ Processing complete")
    else:
        print("✗ Data validation failed")
        print("Please ensure your data files are in the correct location:")
        print(f"Raw data directory: {dataset.raw_dir}")
        print(f"Required files: {list(dataset.get_table_mapping().values())}")

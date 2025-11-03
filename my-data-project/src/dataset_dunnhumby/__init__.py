"""
Dunnhumby Dataset Implementation

This module implements the BaseDatasetInterface for Dunnhumby Complete Journey dataset.
It provides data loading, cleaning, and validation functionality specific to Dunnhumby data.
"""

import duckdb
import pandas as pd
import yaml
from pathlib import Path
import logging
from typing import Dict, List, Optional, Any
import numpy as np
from tqdm import tqdm

# Import the base interface
import sys
sys.path.append(str(Path(__file__).parent.parent))
from dataset_interface import BaseDatasetInterface

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DunnhumbyDataset(BaseDatasetInterface):
    """Dunnhumby dataset implementation following the standard interface."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Dunnhumby dataset loader."""
        super().__init__(config_path)
        
        # Initialize DuckDB connection
        self.con = duckdb.connect(":memory:")
        
        # Create directories
        self.create_directories()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration for Dunnhumby dataset."""
        return {
            'data': {
                'raw_dir': 'data/raw/Dunnhumby',
                'interim_dir': 'data/interim',
                'processed_dir': 'data/processed'
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_table_mapping(self) -> Dict[str, str]:
        """Return mapping of logical table names to CSV file names."""
        return {
            # Core transaction data
            'transactions': 'transaction_data.csv',
            'products': 'product.csv',
            # Customer data
            'demographics': 'hh_demographic.csv',
            # Promotional data
            'causal': 'causal_data.csv',
            # Coupon data
            'coupons': 'coupon.csv',
            'coupon_redemptions': 'coupon_redempt.csv',
            'campaigns': 'campaign_table.csv',
            'campaign_desc': 'campaign_desc.csv'
        }
    
    def clean_transactions(self) -> pd.DataFrame:
        """Clean transaction_data.csv with Dunnhumby-specific logic."""
        logger.info("Cleaning transactions data...")
        
        # Load with DuckDB for efficient processing
        df = self.con.execute(f"""
            SELECT *
            FROM read_csv_auto('{self.raw_dir}/transaction_data.csv')
        """).df()
        
        # Data cleaning steps specific to Dunnhumby
        df = df.assign(
            # Convert transaction time to proper datetime
            TRANS_DATETIME = lambda x: pd.to_datetime(
                x['DAY'].astype(str) + ' ' + x['TRANS_TIME'].str.zfill(4),
                format='%j %H%M'
            ),
            # Extract hour from transaction time
            TRANS_HOUR = lambda x: x['TRANS_TIME'].str[:2].astype(int),
            # Calculate total discount
            TOTAL_DISCOUNT = lambda x: x['RETAIL_DISC'] + x['COUPON_DISC'] + x['COUPON_MATCH_DISC'],
            # Calculate final price
            FINAL_PRICE = lambda x: x['SALES_VALUE'] + x['TOTAL_DISCOUNT']
        )
        
        # Validate values
        assert (df['QUANTITY'] > 0).all(), "Found negative quantities"
        assert (df['FINAL_PRICE'] >= 0).all(), "Found negative final prices"
        
        return df
    
    def clean_products(self) -> pd.DataFrame:
        """Clean product.csv with Dunnhumby-specific logic."""
        logger.info("Cleaning products data...")
        
        df = self.con.execute(f"""
            SELECT *
            FROM read_csv_auto('{self.raw_dir}/product.csv')
        """).df()
        
        # Clean size information
        df['UNIT'] = df['CURR_SIZE_OF_PRODUCT'].str.extract(r'([A-Za-z]+)$')
        df['SIZE_VALUE'] = pd.to_numeric(
            df['CURR_SIZE_OF_PRODUCT'].str.extract(r'([\d.]+)')[0],
            errors='coerce'
        )
        
        # Fill missing values
        df['MANUFACTURER'] = df['MANUFACTURER'].fillna(-1)
        df['DEPARTMENT'] = df['DEPARTMENT'].fillna('Unknown')
        df['BRAND'] = df['BRAND'].fillna('Unknown')
        
        return df
    
    def clean_demographics(self) -> pd.DataFrame:
        """Clean hh_demographic.csv with Dunnhumby-specific logic."""
        logger.info("Cleaning demographics data...")
        
        df = self.con.execute(f"""
            SELECT *
            FROM read_csv_auto('{self.raw_dir}/hh_demographic.csv')
        """).df()
        
        # Convert categorical columns
        cat_cols = ['AGE_DESC', 'MARITAL_STATUS_CODE', 'INCOME_DESC', 
                   'HOMEOWNER_DESC', 'HH_COMP_DESC', 'HOUSEHOLD_SIZE_DESC',
                   'KID_CATEGORY_DESC']
        
        df[cat_cols] = df[cat_cols].fillna('Unknown')
        
        # Extract numeric values where possible
        df['HOUSEHOLD_SIZE'] = df['HOUSEHOLD_SIZE_DESC'].str.extract(r'(\d+)').astype(float)
        df['INCOME_MIN'] = df['INCOME_DESC'].str.extract(r'(\d+)').astype(float)
        
        return df
    
    def clean_causal(self) -> pd.DataFrame:
        """Clean causal_data.csv with Dunnhumby-specific logic."""
        logger.info("Cleaning causal (promotional) data...")
        
        df = self.con.execute(f"""
            SELECT *
            FROM read_csv_auto('{self.raw_dir}/causal_data.csv')
        """).df()
        
        # Convert display to boolean
        df['display'] = df['display'].astype(int).astype(bool)
        
        # Validate week numbers
        assert df['WEEK_NO'].between(1, 53).all(), "Invalid week numbers found"
        
        return df
    
    def clean_coupons(self) -> Dict[str, pd.DataFrame]:
        """Clean coupon-related tables with Dunnhumby-specific logic."""
        logger.info("Cleaning coupon data...")
        
        # Load all coupon-related tables
        coupons = self.con.execute(f"""
            SELECT *
            FROM read_csv_auto('{self.raw_dir}/coupon.csv')
        """).df()
        
        redemptions = self.con.execute(f"""
            SELECT *
            FROM read_csv_auto('{self.raw_dir}/coupon_redempt.csv')
        """).df()
        
        campaigns = self.con.execute(f"""
            SELECT *
            FROM read_csv_auto('{self.raw_dir}/campaign_table.csv')
        """).df()
        
        campaign_desc = self.con.execute(f"""
            SELECT *
            FROM read_csv_auto('{self.raw_dir}/campaign_desc.csv')
        """).df()
        
        return {
            'coupons': coupons,
            'coupon_redemptions': redemptions,
            'campaigns': campaigns,
            'campaign_desc': campaign_desc
        }
    
    def clean_data(self) -> Dict[str, pd.DataFrame]:
        """Clean all Dunnhumby data and return processed DataFrames."""
        logger.info("Starting Dunnhumby data cleaning pipeline...")
        
        # Clean core transaction data
        transactions = self.clean_transactions()
        products = self.clean_products()
        
        # Clean customer data
        demographics = self.clean_demographics()
        
        # Clean promotional data
        causal = self.clean_causal()
        
        # Clean coupon data
        coupon_data = self.clean_coupons()
        
        # Combine all data
        all_data = {
            'transactions': transactions,
            'products': products,
            'demographics': demographics,
            'causal': causal
        }
        all_data.update(coupon_data)
        
        return all_data
    
    def validate_data(self) -> bool:
        """Validate Dunnhumby data integrity."""
        logger.info("Validating Dunnhumby data integrity...")
        
        try:
            # Check if all required files exist
            table_mapping = self.get_table_mapping()
            for table_name, file_name in table_mapping.items():
                file_path = self.raw_dir / file_name
                if not file_path.exists():
                    logger.error(f"Missing required file: {file_name}")
                    return False
            
            # Load and validate coupon referential integrity
            redemptions = self.con.execute(f"""
                SELECT *
                FROM read_csv_auto('{self.raw_dir}/coupon_redempt.csv')
            """).df()
            
            coupons = self.con.execute(f"""
                SELECT *
                FROM read_csv_auto('{self.raw_dir}/coupon.csv')
            """).df()
            
            campaign_desc = self.con.execute(f"""
                SELECT *
                FROM read_csv_auto('{self.raw_dir}/campaign_desc.csv')
            """).df()
            
            # Validate referential integrity
            if not set(redemptions['COUPON_UPC']).issubset(set(coupons['COUPON_UPC'])):
                logger.error("Found redemptions for non-existent coupons")
                return False
            
            if not set(redemptions['CAMPAIGN']).issubset(set(campaign_desc['CAMPAIGN'])):
                logger.error("Found redemptions for non-existent campaigns")
                return False
            
            logger.info("Data validation passed!")
            return True
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False
    
    def process_all(self):
        """Run full Dunnhumby cleaning pipeline and save results."""
        if not self.validate_data():
            raise ValueError("Data validation failed - cannot proceed with processing")
        
        # Clean all data
        all_data = self.clean_data()
        
        # Save all cleaned datasets
        for name, df in all_data.items():
            self.save_parquet(df, name)
            logger.info(f"Saved {name}.parquet ({df.shape[0]:,} rows)")
        
        logger.info("Dunnhumby data cleaning pipeline completed!")


# Factory function to create dataset instances
def create_dataset(config_path: Optional[str] = None) -> DunnhumbyDataset:
    """Factory function to create DunnhumbyDataset instance."""
    return DunnhumbyDataset(config_path)


# For backward compatibility and easy imports
DunnhumbyDataCleaner = DunnhumbyDataset

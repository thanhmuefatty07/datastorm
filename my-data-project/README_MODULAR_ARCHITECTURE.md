# Modular Dataset Architecture

This document explains the new modular dataset architecture that allows easy switching between different datasets while maintaining the same processing pipeline.

## Overview

The original codebase was tightly coupled to the Dunnhumby dataset. The new architecture separates dataset-specific logic from the core processing pipeline, making it easy to:

- **Switch datasets** without changing core logic
- **Maintain consistent output** regardless of dataset
- **Extend functionality** for new datasets
- **Keep backward compatibility** with existing code

## Architecture Components

### 1. Base Dataset Interface (`src/dataset_interface/`)

Defines the standard interface that all datasets must implement:

```python
from dataset_interface import BaseDatasetInterface

class YourDataset(BaseDatasetInterface):
    def get_table_mapping(self) -> Dict[str, str]:
        # Return mapping of logical names to file names
        pass
        
    def clean_data(self) -> Dict[str, pd.DataFrame]:
        # Clean and return processed DataFrames
        pass
        
    def validate_data(self) -> bool:
        # Validate data integrity
        pass
```

### 2. Dataset Implementations

#### Dunnhumby Dataset (`src/dataset_dunnhumby/`)

- **Purpose**: Complete implementation for Dunnhumby Complete Journey dataset
- **Configuration**: `configs/dataset_dunnhumby_paths.yaml`
- **Features**: 
  - Transaction data cleaning
  - Product data enrichment
  - Demographics processing
  - Promotional data handling
  - Coupon analysis
  - Referential integrity validation

```python
from dataset_dunnhumby import create_dataset

# Create dataset instance
dataset = create_dataset("configs/dataset_dunnhumby_paths.yaml")

# Process all data
dataset.process_all()
```

### 3. Modular Tools

#### Data Preview (`src/w4/peek_data_modular.py`)

```bash
python src/w4/peek_data_modular.py
```

- Works with any dataset implementing the interface
- Automatically discovers available tables
- Shows schema and sample data
- Configurable through dataset config files

#### Data Cleaning (`src/w4/cleaning/clean_modular.py`)

```bash
python src/w4/cleaning/clean_modular.py configs/dataset_dunnhumby_paths.yaml
```

- Dataset-agnostic cleaning pipeline
- Automatic validation before processing
- Consistent output format regardless of dataset
- Configurable processing parameters

## Configuration System

### Dataset-Specific Configurations

Each dataset has its own configuration file:

```yaml
# configs/dataset_dunnhumby_paths.yaml
data:
  raw_dir: "data/raw/Dunnhumby"
  interim_dir: "data/interim"
  processed_dir: "data/processed"

dataset:
  name: "Dunnhumby Complete Journey"
  required_files:
    - "transaction_data.csv"
    - "product.csv"
    # ... more files

processing:
  sample_size: 200000
  chunk_size: 10000
  cleaning:
    extract_datetime_features: true
    calculate_derived_metrics: true
```

## How to Switch Datasets

### Option 1: Using Existing Interface

For datasets with similar structure to Dunnhumby:

1. **Create new config file**:
   ```yaml
   # configs/dataset_your_data_paths.yaml
   data:
     raw_dir: "data/raw/YourDataset"
     # ... other paths
   ```

2. **Update file mapping** (if different):
   ```python
   # Modify dataset_dunnhumby/__init__.py or create new implementation
   def get_table_mapping(self):
       return {
           'transactions': 'your_transactions.csv',
           'products': 'your_products.csv',
           # ... your mappings
       }
   ```

3. **Run with new config**:
   ```bash
   python src/w4/cleaning/clean_modular.py configs/dataset_your_data_paths.yaml
   ```

### Option 2: Creating New Dataset Implementation

For completely different datasets:

1. **Create new dataset module**:
   ```python
   # src/dataset_your_data/__init__.py
   from dataset_interface import BaseDatasetInterface
   
   class YourDataset(BaseDatasetInterface):
       def get_table_mapping(self):
           return {'main_table': 'your_data.csv'}
           
       def clean_data(self):
           # Your specific cleaning logic
           pass
           
       def validate_data(self):
           # Your validation logic
           return True
   
   def create_dataset(config_path=None):
       return YourDataset(config_path)
   ```

2. **Create configuration**:
   ```yaml
   # configs/dataset_your_data_paths.yaml
   data:
     raw_dir: "data/raw/YourDataset"
   ```

3. **Update modular scripts**:
   ```python
   # In clean_modular.py, add:
   elif dataset_type == "your_data":
       from dataset_your_data import create_dataset
       dataset = create_dataset(dataset_config)
   ```

## Migration from Original Code

### Backward Compatibility

The original cleaning script (`clean_dunnhumby.py`) is preserved and still works. The new modular system provides:

- **Same output format**: Parquet files in same locations
- **Same data quality**: Identical cleaning logic preserved
- **Same performance**: Uses same DuckDB backend

### Migration Steps

1. **Replace imports**:
   ```python
   # Old:
   from w4.cleaning.clean_dunnhumby import DunnhumbyDataCleaner
   
   # New:
   from dataset_dunnhumby import create_dataset
   ```

2. **Update initialization**:
   ```python
   # Old:
   cleaner = DunnhumbyDataCleaner("configs/paths.yaml")
   
   # New:
   dataset = create_dataset("configs/dataset_dunnhumby_paths.yaml")
   ```

3. **Use new methods**:
   ```python
   # Old:
   cleaner.process_all()
   
   # New:
   dataset.process_all()  # Same method name!
   ```

## Benefits of New Architecture

### ✅ **Easy Dataset Switching**
- Change config file path
- No code changes needed for core pipeline
- Consistent output format

### ✅ **Maintainable Code**
- Clear separation of concerns
- Standardized interfaces
- Reusable components

### ✅ **Extensible Design**
- Add new datasets without touching existing code
- Plugin-like architecture
- Support for different data formats

### ✅ **Backward Compatible**
- Existing code continues to work
- Gradual migration possible
- No breaking changes

## Example Workflows

### Processing Dunnhumby Data

```bash
# Preview data
python src/w4/peek_data_modular.py

# Clean data
python src/w4/cleaning/clean_modular.py configs/dataset_dunnhumby_paths.yaml

# Results in data/processed/*.parquet
```

### Adding New Dataset

```bash
# 1. Create implementation
mkdir src/dataset_newdata
touch src/dataset_newdata/__init__.py

# 2. Create config
touch configs/dataset_newdata_paths.yaml

# 3. Test
python src/w4/cleaning/clean_modular.py configs/dataset_newdata_paths.yaml
```

## File Structure

```
my-data-project/
├── src/
│   ├── dataset_interface/          # Base interface
│   │   └── __init__.py
│   ├── dataset_dunnhumby/          # Dunnhumby implementation
│   │   └── __init__.py
│   └── w4/
│       ├── peek_data_modular.py    # Modular data preview
│       └── cleaning/
│           ├── clean_modular.py     # Modular cleaning
│           └── clean_dunnhumby.py   # Original (preserved)
├── configs/
│   ├── paths.yaml                  # Original config
│   └── dataset_dunnhumby_paths.yaml # New Dunnhumby config
└── README_MODULAR_ARCHITECTURE.md  # This file
```

## Testing

### Verify Same Output

```python
# Test that new system produces same results as original
import pandas as pd

# Run original
# ... (run original clean_dunnhumby.py)
original_transactions = pd.read_parquet('data/processed/transactions_original.parquet')

# Run new modular system
dataset = create_dataset('configs/dataset_dunnhumby_paths.yaml')
dataset.process_all()
new_transactions = pd.read_parquet('data/processed/transactions.parquet')

# Compare
assert original_transactions.equals(new_transactions)
print("✅ Output identical!")
```

## Next Steps

1. **Test the new system** with your Dunnhumby data
2. **Validate output consistency** against original system
3. **Create new dataset implementations** for other data sources
4. **Integrate with existing w4 pipeline** components
5. **Add more dataset-specific features** as needed

---

*This modular architecture ensures your data pipeline remains flexible and maintainable while preserving all existing functionality.*

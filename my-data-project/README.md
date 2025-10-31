# Data Analysis Project

Analysis of retail data focusing on promotion effectiveness and price elasticity.

## Project Structure

```
my-data-project/
├── data/               # Data files (gitignored)
│   ├── interim/       # Intermediate processed data
│   ├── processed/     # Final processed data
│   └── raw/          # Raw data files
├── reports/           # Generated analysis reports
│   └── w4/           # Workstream 4 outputs
│       └── plots/    # Generated figures
├── src/              # Source code
│   └── w4/          # Workstream 4 modules
│       ├── cleaning/     # Data cleaning scripts
│       ├── features/     # Feature engineering
│       ├── modeling/     # Statistical models
│       ├── qa/          # Quality assurance
│       └── tools/       # Utility functions
└── logs/             # Log files (gitignored)
```

## Key Components

### Data Processing
- `src/w4/cleaning/`: Data validation and cleaning pipelines
- `src/w4/features/`: Feature engineering and transformation logic
- `src/w4/qa/`: Data quality checks and validation

### Analysis
- `src/w4/modeling/`: Core analytical models
  - `promo_lift.py`: Promotion effectiveness analysis using DID
  - Other modeling scripts for price elasticity

### Utilities
- `src/w4/tools/`: Helper functions and common utilities

## Setup

1. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
.venv\Scripts\Activate.ps1  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Guidelines

- Use Python 3.8+
- Follow PEP 8 style guide
- Run pre-commit hooks before committing
- Update requirements.txt when adding dependencies

## Code Quality

This project uses several tools to maintain code quality:
- Black for code formatting
- isort for import sorting
- flake8 for style guide enforcement
- mypy for type checking

All configured via pre-commit hooks.
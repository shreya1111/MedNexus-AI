# Datasets Directory

This directory is reserved for storing training and testing datasets for ML models.

## Structure

```
datasets/
├── raw/           # Raw, unprocessed data files
├── processed/     # Cleaned and preprocessed datasets
└── external/      # External datasets from third parties
```

## Usage

- Place CSV, JSON, or other data files here
- Use DVC for version control of large datasets
- Document data sources and preprocessing steps in notebooks

## Current Status

Empty — datasets will be added during ML model development phase.

## Security Note

Never commit sensitive patient data. Use synthetic or anonymized datasets only.

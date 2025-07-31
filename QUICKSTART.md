# KBI Labs Context-Aware Intelligence Platform - Quick Start

## 1. Upload DSBS Data
```bash
./scripts/upload_dsbs_data.sh path/to/your/All_DSBS_processed_chunk_*.csv
```

## 2. Process Data
```bash
./scripts/run_dsbs_processing.sh
```

## 3. Generate Test Tokens
```bash
python scripts/generate_test_tokens.py
```

## 4. Test API Endpoints

### PE Firm View
```bash
curl -H "Authorization: Bearer <PE_TOKEN>" \
     http://localhost:8000/api/v2/companies/{UEI}/intelligence
```

### SMB Owner View
```bash
curl -H "Authorization: Bearer <SMB_TOKEN>" \
     http://localhost:8000/api/v2/companies/{UEI}/intelligence
```

### Search High-Risk Companies (PE Only)
```bash
curl -H "Authorization: Bearer <PE_TOKEN>" \
     "http://localhost:8000/api/v2/intelligence/search?min_succession_risk=7&state=FL"
```

## 5. Access Documentation
- API Docs: http://localhost:8000/docs
- Monitoring: http://localhost:3000 (admin/admin)

## Context-Aware Features

The API automatically adjusts responses based on user type:

- **PE Firms** see: Valuation multiples, acquisition scores, due diligence flags
- **SMB Owners** see: Health grades, peer comparisons, improvement actions
- **API Developers** see: Raw data with all calculations

## Subscription Tiers

- **Free**: 10 requests/min, basic features
- **Professional**: 50 requests/min, peer benchmarking
- **Enterprise**: 500 requests/min, all features + overrides

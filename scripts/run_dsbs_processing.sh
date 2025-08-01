#!/bin/bash
# Run DSBS processing pipeline

echo "🔄 Running DSBS Processing Pipeline"
echo "=================================="

# Run inside container
docker exec -it kbi_api python -m src.data_processors.dsbs_processor

echo "✅ Processing complete!"

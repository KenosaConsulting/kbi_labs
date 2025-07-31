#!/bin/bash
# Helper script to upload DSBS CSV files

echo "📤 DSBS Data Upload Helper"
echo "========================"

if [ $# -eq 0 ]; then
    echo "Usage: ./upload_dsbs_data.sh path/to/csv/files/*.csv"
    exit 1
fi

# Upload each file
for file in "$@"; do
    if [ -f "$file" ]; then
        echo "Uploading $file..."
        docker cp "$file" kbi_api:/app/data/dsbs_raw/
        echo "✅ Uploaded $(basename "$file")"
    else
        echo "❌ File not found: $file"
    fi
done

echo "✅ Upload complete!"

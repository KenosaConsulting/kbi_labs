#!/bin/bash
# KBI Labs Complete Setup Script
# Sets up and runs the complete enrichment pipeline

echo "========================================"
echo "KBI LABS COMPLETE ENRICHMENT SETUP"
echo "========================================"

# Check if running on Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    echo "This script is designed for Ubuntu/Debian systems"
    exit 1
fi

# Function to check and set API keys
check_api_keys() {
    echo -e "\n📋 Checking API Keys..."
    
    MISSING_KEYS=()
    
    # Check each required API key
    if [ -z "$SAM_GOV_API_KEY" ]; then
        MISSING_KEYS+=("SAM_GOV_API_KEY")
    fi
    
    if [ -z "$CENSUS_API_KEY" ]; then
        MISSING_KEYS+=("CENSUS_API_KEY")
    fi
    
    if [ -z "$USPTO_API_KEY" ]; then
        MISSING_KEYS+=("USPTO_API_KEY")
    fi
    
    if [ -z "$NSF_API_KEY" ]; then
        MISSING_KEYS+=("NSF_API_KEY")
    fi
    
    if [ -z "$FRED_API_KEY" ]; then
        MISSING_KEYS+=("FRED_API_KEY")
    fi
    
    # If keys are missing, prompt for them
    if [ ${#MISSING_KEYS[@]} -gt 0 ]; then
        echo "The following API keys are missing:"
        for key in "${MISSING_KEYS[@]}"; do
            echo "  - $key"
        done
        
        echo -e "\nWould you like to enter them now? (y/n)"
        read -r response
        
        if [[ "$response" == "y" ]]; then
            for key in "${MISSING_KEYS[@]}"; do
                echo -n "Enter $key: "
                read -r value
                export "$key=$value"
            done
            
            # Save to .env file
            echo -e "\nSaving API keys to .env file..."
            cat > .env << EOF
# KBI Labs API Keys
SAM_GOV_API_KEY=$SAM_GOV_API_KEY
CENSUS_API_KEY=$CENSUS_API_KEY
USPTO_API_KEY=$USPTO_API_KEY
NSF_API_KEY=$NSF_API_KEY
FRED_API_KEY=$FRED_API_KEY

# Database Configuration
DATABASE_URL=postgresql://ubuntu:kbi_labs_2024@localhost:5432/kbi_enriched_full

# Processing Configuration
MAX_CONCURRENT_REQUESTS=50
BATCH_SIZE=100

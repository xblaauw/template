#!/bin/bash

set -e  # Exit on any error

# List all Python scripts in order of execution
SCRIPTS=(
    # "app.py"
    # Add more scripts here as needed
)

# Run each script
for script in "${SCRIPTS[@]}"; do
    echo "Running $script..."
    python -u "$script"  # -u for unbuffered output
    
    # Check exit status
    if [ $? -ne 0 ]; then
        echo "Error: $script failed"
        exit 1
    fi
done

streamlit run app.py

echo "All scripts completed successfully"

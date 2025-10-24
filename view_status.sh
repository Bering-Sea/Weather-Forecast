#!/bin/bash
# View Weather Forecast API Health Status

echo "Weather Forecast API Health Status"
echo "===================================="
echo ""

# Check if report file exists
if [ -f "./data/forecast_report.txt" ]; then
    cat ./data/forecast_report.txt
else
    echo "No status report available yet."
    echo "The report will be generated after the first forecast collection."
fi

echo ""
echo "Press Ctrl+C to exit"

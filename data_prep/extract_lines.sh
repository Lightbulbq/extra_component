#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 input_file num_lines output_file"
    exit 1
fi

# Assign arguments to variables
input_file=$1
num_lines=$2
output_file=$3

# Check if the input file exists
if [ ! -f "$input_file" ]; then
    echo "Input file not found!"
    exit 1
fi

# Extract the first n lines from the input file and save to the output file
head -n "$num_lines" "$input_file" > "$output_file"

# Print a success message
echo "Extracted the first $num_lines lines from $input_file and saved to $output_file"

#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 input_file output_file"
    exit 1
fi

# Assign arguments to variables
input_file=$1
output_file=$2

# Check if the input file exists
if [ ! -f "$input_file" ]; then
    echo "Input file not found!"
    exit 1
fi

# Shuffle the lines in the input file and write to the output file
shuf "$input_file" -o "$output_file"

# Print a success message
echo "Shuffled lines from $input_file and saved to $output_file"

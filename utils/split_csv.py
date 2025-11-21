#!/usr/bin/env python3
import os
import sys

def split_csv(input_file, max_size_mb=200):
    """Split a CSV file into smaller files while preserving headers."""
    max_size_bytes = max_size_mb * 1024 * 1024
    base_name = os.path.splitext(input_file)[0]
    
    with open(input_file, 'r', encoding='utf-8') as f:
        header = f.readline()
        
        file_num = 0
        current_size = 0
        output_file = None
        
        for line in f:
            # Start a new file if needed
            if output_file is None or current_size >= max_size_bytes:
                if output_file:
                    output_file.close()
                
                output_filename = f"{base_name}_{file_num:02d}.csv"
                print(f"Creating {output_filename}...")
                output_file = open(output_filename, 'w', encoding='utf-8')
                output_file.write(header)
                current_size = len(header.encode('utf-8'))
                file_num += 1
            
            output_file.write(line)
            current_size += len(line.encode('utf-8'))
        
        if output_file:
            output_file.close()
    
    print(f"Split {input_file} into {file_num} files")

if __name__ == "__main__":
    files = ["mock-data/GUIDE_Test.csv", "mock-data/GUIDE_Train.csv"]
    
    for file in files:
        if os.path.exists(file):
            print(f"\nProcessing {file}...")
            split_csv(file)
        else:
            print(f"File not found: {file}")

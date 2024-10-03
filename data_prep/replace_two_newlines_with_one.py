import fire
import json

def replace_newlines_in_jsonl(file_path):
    # Open the JSONL file and process it line by line
    with open(file_path, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    
    # Iterate over each line, parse the JSON, modify the "raw_content" key
    for line in lines:
        json_obj = json.loads(line)  # Parse the JSON object from the line
        
        # Replace \n\n with \n only in the "raw_content" key if it exists
        if 'raw_content' in json_obj:
            json_obj['raw_content'] = json_obj['raw_content'].replace('\n\n', '\n')

        updated_lines.append(json.dumps(json_obj) + '\n')  # Re-convert to JSON string and keep the newline

    # Write the updated lines back to the file
    with open(file_path, 'w') as file:
        file.writelines(updated_lines)

    print("Replacement in 'raw_content' key complete!")

if __name__ == '__main__':
    fire.Fire(replace_newlines_in_jsonl)


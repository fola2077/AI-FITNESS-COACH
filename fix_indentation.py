import re

def fix_indentation():
    # Path to the file
    file_path = r'c:\Users\KAMI\Downloads\AI-FITNESS-COACH\src\gui\main_window.py'
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix indentation in update_ui methods
    # Look for update_ui with wrong indentation
    pattern = r'(\s+)def update_ui\(self, live_metrics: dict\):\n(\s+)"""'
    
    # Find all occurrences
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        print("No matching patterns found. Check the file manually.")
        return
    
    # Process the file in reverse order to avoid offset issues
    for match in reversed(matches):
        # Get the correct indentation from the method definition
        indentation = match.group(1)
        
        # Extract the start position of the method
        start_pos = match.start()
        
        # Find the end of the method (next def or end of file)
        next_def_pos = content.find("\n" + indentation + "def ", start_pos + 1)
        if next_def_pos == -1:
            # If no next def, take until end of file
            method_block = content[start_pos:]
        else:
            method_block = content[start_pos:next_def_pos]
        
        # Split the method block into lines
        lines = method_block.split("\n")
        
        # First line (method definition) is already correctly indented
        fixed_lines = [lines[0]]
        
        # Fix indentation for all other lines
        for i in range(1, len(lines)):
            # Remove existing indentation
            stripped = lines[i].lstrip()
            if stripped:  # If not an empty line
                # Add correct indentation plus 4 spaces for method body
                fixed_lines.append(indentation + "    " + stripped)
            else:
                fixed_lines.append("")  # Keep empty lines as is
        
        # Combine the fixed lines
        fixed_method = "\n".join(fixed_lines)
        
        # Replace the original method with the fixed version
        content = content[:start_pos] + fixed_method + content[start_pos + len(method_block):]
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("File updated successfully!")

# Run the fix
fix_indentation()

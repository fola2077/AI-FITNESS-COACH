import json
import re
import os
from datetime import datetime
import pandas as pd

notebook_path = "Eval.ipynb"

def extract_outputs_from_notebook(notebook_path):
    """Extract actual output values from Jupyter notebook cells."""
    
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        return extract_from_jupyter_format(notebook)
    except json.JSONDecodeError:
        # Handle VSCode notebook format
        with open(notebook_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return extract_from_vscode_format(content)

def extract_from_jupyter_format(notebook):
    """Extract outputs from standard Jupyter notebook format."""
    outputs = []
    
    for cell_num, cell in enumerate(notebook.get('cells', []), 1):
        if cell.get('cell_type') == 'code':
            cell_outputs = cell.get('outputs', [])
            
            for output in cell_outputs:
                # Extract text/plain output
                if 'text' in output:
                    text_output = output['text']
                    if isinstance(text_output, list):
                        text_output = ''.join(text_output)
                    
                    outputs.append({
                        'cell': cell_num,
                        'type': 'output',
                        'content': text_output.strip()
                    })
                
                # Extract stdout streams
                elif output.get('output_type') == 'stream' and output.get('name') == 'stdout':
                    stream_text = output.get('text', '')
                    if isinstance(stream_text, list):
                        stream_text = ''.join(stream_text)
                    
                    outputs.append({
                        'cell': cell_num,
                        'type': 'stdout',
                        'content': stream_text.strip()
                    })
                
                # Extract display_data and execute_result
                elif output.get('output_type') in ['display_data', 'execute_result']:
                    data = output.get('data', {})
                    if 'text/plain' in data:
                        plain_text = data['text/plain']
                        if isinstance(plain_text, list):
                            plain_text = ''.join(plain_text)
                        
                        outputs.append({
                            'cell': cell_num,
                            'type': output.get('output_type'),
                            'content': plain_text.strip()
                        })
    
    return outputs

def extract_from_vscode_format(content):
    """Extract outputs from VSCode notebook format."""
    outputs = []
    
    # Pattern to find VSCode cells with outputs
    cell_pattern = r'<VSCode\.Cell[^>]*language="python"[^>]*>(.*?)</VSCode\.Cell>'
    cells = re.findall(cell_pattern, content, re.DOTALL)
    
    for cell_num, cell_content in enumerate(cells, 1):
        # Look for output sections within each cell
        output_patterns = [
            r'<VSCode\.Output[^>]*>(.*?)</VSCode\.Output>',
            r'<output[^>]*>(.*?)</output>',
            r'<stdout>(.*?)</stdout>',
            r'<stderr>(.*?)</stderr>'
        ]
        
        for pattern in output_patterns:
            matches = re.findall(pattern, cell_content, re.DOTALL)
            for match in matches:
                # Clean up HTML entities and formatting
                cleaned_output = clean_output_text(match)
                if cleaned_output.strip():
                    outputs.append({
                        'cell': cell_num,
                        'type': 'output',
                        'content': cleaned_output.strip()
                    })
    
    return outputs

def clean_output_text(text):
    """Clean up output text from HTML entities and formatting."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Replace common HTML entities
    replacements = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }
    
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove excessive blank lines
    text = re.sub(r'[ \t]+', ' ', text)      # Normalize spaces
    
    return text

def create_markdown_from_outputs(outputs, notebook_name):
    """Create markdown document from extracted outputs."""
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    markdown_content = f"""# Notebook Output Results - {notebook_name}

This document contains the actual output results from running the Jupyter notebook analysis.

Generated on: {current_time}

---

"""
    
    if not outputs:
        markdown_content += """
## No Output Found

⚠️ **Warning**: No output was found in the notebook. This could mean:

1. The notebook hasn't been executed yet
2. The notebook format is not supported
3. All outputs have been cleared

**Recommendation**: Run all cells in the notebook first, then re-run this extraction script.

"""
        return markdown_content
    
    current_cell = None
    for output in outputs:
        if output['cell'] != current_cell:
            current_cell = output['cell']
            markdown_content += f"\n## Cell {current_cell} Output\n\n"
        
        content = output['content']
        
        # Format different types of content
        if content.startswith('🎯') or content.startswith('📊') or content.startswith('✅'):
            markdown_content += f"### {content}\n\n"
        elif '=' * 20 in content or '=' * 30 in content or '=' * 40 in content:
            markdown_content += f"\n---\n\n"
        elif any(keyword in content.lower() for keyword in ['dataframe', 'series', 'array']):
            markdown_content += f"```\n{content}\n```\n\n"
        elif content.startswith('   ') or '\n   ' in content:
            # Likely formatted output or data
            markdown_content += f"```\n{content}\n```\n\n"
        else:
            markdown_content += f"{content}\n\n"
    
    return markdown_content

def main():
    """Main function to extract outputs and create markdown."""
    
    notebook_path = "Eval.ipynb"
    
    if not os.path.exists(notebook_path):
        print(f"❌ Notebook file not found: {notebook_path}")
        return
    
    print("🔍 Extracting actual outputs from notebook...")
    
    try:
        outputs = extract_outputs_from_notebook(notebook_path)
        
        if not outputs:
            print("⚠️ No outputs found in the notebook")
            print("   Make sure the notebook has been executed and contains output cells")
            
            # Create a warning document
            notebook_name = os.path.basename(notebook_path)
            markdown_content = create_markdown_from_outputs([], notebook_name)
        else:
            print(f"✅ Found {len(outputs)} output entries")
            
            # Create markdown document
            notebook_name = os.path.basename(notebook_path)
            markdown_content = create_markdown_from_outputs(outputs, notebook_name)
        
        # Save to file
        output_file = "notebook_actual_results.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Results document created: {output_file}")
        
        if outputs:
            print(f"📊 Document contains {len(outputs)} output entries from {len(set(out['cell'] for out in outputs))} cells")
            
            # Show preview
            print(f"\n📋 PREVIEW OF EXTRACTED RESULTS:")
            for i, output in enumerate(outputs[:3]):
                preview = output['content'][:100] + "..." if len(output['content']) > 100 else output['content']
                print(f"   Cell {output['cell']}: {preview}")
            
            if len(outputs) > 3:
                print(f"   ... and {len(outputs) - 3} more output entries")
        else:
            print("\n💡 TIP: Execute all notebook cells first, then run this script again")
            
    except Exception as e:
        print(f"❌ Error processing notebook: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
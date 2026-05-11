import os
import re

agent_dir = 'core/agents'
files_to_fix = [
    'analyst.py', 'content_writer.py', 'distributor.py', 
    'editor.py', 'reviewer.py', 'script_writer.py',
    'topic_curator.py', 'visual_designer.py'
]

for filename in files_to_fix:
    filepath = os.path.join(agent_dir, filename)
    print(f'Fixing {filename}...')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    first_triple_quote = -1
    second_triple_quote = -1
    for i, line in enumerate(lines):
        if '"""' in line:
            if first_triple_quote == -1:
                first_triple_quote = i
            else:
                second_triple_quote = i
                break
    
    if first_triple_quote == -1 or second_triple_quote == -1:
        print(f'  Could not find triple quotes')
        continue
    
    import_start = -1
    for i in range(second_triple_quote + 1, len(lines)):
        if lines[i].strip().startswith(('import ', 'from ')):
            import_start = i
            break
    
    if import_start == -1:
        print(f'  Could not find imports')
        continue
    
    between_lines = lines[second_triple_quote + 1:import_start]
    has_chinese = any(re.search(r'[一-鿿]', line) for line in between_lines)
    
    if not has_chinese:
        print(f'  No Chinese text to fix')
        continue
    
    new_lines = []
    new_lines.extend(lines[:first_triple_quote + 1])
    new_lines.extend(lines[first_triple_quote + 1:second_triple_quote])
    new_lines.append('"""')
    new_lines.extend(between_lines)
    new_lines.append('"""')
    new_lines.extend(lines[import_start:])
    
    new_content = '\n'.join(new_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f'  Fixed!')

print('Done!')

# -*- coding: utf-8 -*-
"""Fix agent files encoding issues."""
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

    # Find all lines with """
    triple_quote_lines = []
    for i, line in enumerate(lines):
        if '"""' in line:
            triple_quote_lines.append(i)

    print(f'  Found {len(triple_quote_lines)} triple quotes at lines: {[x+1 for x in triple_quote_lines]}')

    if len(triple_quote_lines) < 2:
        print(f'  Not enough triple quotes, skipping')
        continue

    # Find imports
    import_start = -1
    for i in range(len(lines)):
        if lines[i].strip().startswith(('import ', 'from ')):
            import_start = i
            break

    if import_start == -1:
        print(f'  Could not find imports')
        continue

    print(f'  Imports start at line {import_start + 1}')

    # Check if there's Chinese text between last triple quote and imports
    last_triple_quote = -1
    for i in range(import_start - 1, -1, -1):
        if '"""' in lines[i]:
            last_triple_quote = i
            break

    if last_triple_quote == -1:
        print(f'  Could not find triple quote before imports')
        continue

    print(f'  Last triple quote at line {last_triple_quote + 1}')

    between_lines = lines[last_triple_quote + 1:import_start]
    has_chinese = any(re.search(r'[一-鿿]', line) for line in between_lines)

    if not has_chinese:
        print(f'  No Chinese text between triple quote and imports')
        continue

    # Reconstruct: merge docstring and Chinese description
    # Find first triple quote (the module docstring start)
    first_triple_quote = triple_quote_lines[0]

    new_lines = []
    new_lines.append('# -*- coding: utf-8 -*-')
    new_lines.append('"""')
    # Line 0 content without the opening """
    first_line_content = lines[0].replace('"""', '').strip()
    new_lines.append(first_line_content)

    # Content between first and last triple quote (excluding the SYSTEM_PROMPT part)
    # We need to include lines from first_triple_quote+1 to last_triple_quote-1
    # but these contain the SYSTEM_PROMPT

    # Let's take a different approach: find lines between first and last triple quote
    # that are NOT part of the system prompt

    # Actually, the structure is:
    # Line 0: """Agent description
    # Line 1: SYSTEM_PROMPT = """
    # Line 2: \
    # ...
    # Line X: """  (closes SYSTEM_PROMPT)
    # Line X+1: (empty)
    # Line X+2 to Y: Chinese description
    # Line Y+1: """ (closes the first docstring)
    # Line Y+2: import

    # Wait, that's not right either. Let me look at the actual structure.

    # Actually looking at the file:
    # Line 0: """小编 TopicCurator -- 选题总编 Agent。
    # Line 1: SYSTEM_PROMPT = """
    # Line 2: \
    # ...
    # Line 27: """  (closes SYSTEM_PROMPT)
    # Line 28: (empty)
    # Line 29: (empty)
    # Line 30: 小编是NewsAI的选题总编，负责：
    # ...
    # Line 34: 4. 写入选题库，状态为"待选"
    # Line 35: """  (this is the problematic one - closes the first docstring)
    # Line 36: (empty)
    # Line 37: import json

    # So the fix is:
    # - Line 0 should be a complete docstring: """Agent description."""
    # - OR move the Chinese description inside the docstring

    # Let's change Line 0 to be a proper single-line docstring
    # and keep everything else as is

    # Actually, better approach: make lines 0-34 all one big docstring
    # by removing the """ at line 27 and line 35

    # Find the SYSTEM_PROMPT closing quote
    system_prompt_start = triple_quote_lines[1]  # Line 1: SYSTEM_PROMPT = """
    system_prompt_end = -1
    for i in range(system_prompt_start + 1, len(triple_quote_lines)):
        if triple_quote_lines[i] > system_prompt_start:
            system_prompt_end = triple_quote_lines[i]
            break

    print(f'  SYSTEM_PROMPT ends at line {system_prompt_end + 1}')

    # The Chinese description is after system_prompt_end and before the next """
    # Let's just make everything from line 0 to the line before imports one big docstring

    new_lines = []
    new_lines.append('# -*- coding: utf-8 -*-')
    new_lines.append('"""')

    # Add content from line 0 (without opening """), up to imports
    line_0_content = lines[0].replace('"""', '').strip()
    new_lines.append(line_0_content)
    new_lines.append('')  # Empty line

    # Add lines 1 to import_start-1, but skip any standalone """ that would close the docstring
    for i in range(1, import_start):
        line = lines[i]
        if line.strip() == '"""':
            # Skip standalone triple quotes - we'll add one at the end
            continue
        new_lines.append(line)

    # Close the docstring
    new_lines.append('"""')
    new_lines.append('')  # Empty line before imports

    # Add imports and rest
    new_lines.extend(lines[import_start:])

    new_content = '\n'.join(new_lines)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f'  Fixed!')

print('Done!')

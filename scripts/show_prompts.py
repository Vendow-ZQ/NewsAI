"""显示所有Agent的System Prompt"""
import os
import re
from pathlib import Path

def show_all_prompts():
    """显示所有Agent的Prompt"""
    agents_dir = Path('core/agents')

    print("="*80)
    print("NewsAI Agent System Prompt Summary")
    print("="*80)
    print()

    agent_files = [
        ('trend_scout.py', 'Xiao Shao (TrendScout)'),
        ('topic_curator.py', 'Xiao Bian (TopicCurator)'),
        ('content_writer.py', 'Xiao Wen (ContentWriter)'),
        ('visual_designer.py', 'Xiao Tu (VisualDesigner)'),
        ('script_writer.py', 'Xiao Bo (ScriptWriter)'),
        ('reviewer.py', 'Xiao Shen (Reviewer)'),
        ('editor.py', 'Xiao Gai (Editor)'),
        ('distributor.py', 'Xiao Fa (Distributor)'),
        ('analyst.py', 'Xiao Shu (Analyst)'),
    ]

    for filename, agent_name in agent_files:
        filepath = agents_dir / filename
        if filepath.exists():
            print(f"\n{'='*80}")
            print(f"Agent: {agent_name}")
            print(f"File: {filepath}")
            print('='*80)

            content = filepath.read_text(encoding='utf-8')

            # Find _build_prompt methods
            methods = re.findall(r'def (_build\w*?_prompt)\([^)]*\)', content)
            if methods:
                print(f"\nPrompt Methods: {', '.join(methods)}")

                # Show first few lines of each method
                for method in methods[:2]:
                    print(f"\n--- {method} Preview ---")
                    # Find the method
                    start = content.find(f'def {method}(')
                    if start != -1:
                        # Get next 500 characters
                        snippet = content[start:start+500]
                        # Find return statement
                        ret_start = snippet.find('return f"""')
                        if ret_start == -1:
                            ret_start = snippet.find("return f'")
                        if ret_start != -1:
                            # Show first 300 chars of return
                            ret_part = snippet[ret_start:ret_start+300]
                            print(ret_part.replace('return f"""', '').replace("return f'", '')[:250] + "...")
                        else:
                            print("  (Dynamic prompt building)")

    print("\n" + "="*80)
    print("How to view full prompts:")
    print("="*80)
    print("1. Open the agent file in core/agents/")
    print("2. Find the _build_xxx_prompt method")
    print("3. The return f\"\"\"...\"\"\" contains the full prompt")
    print()

if __name__ == "__main__":
    show_all_prompts()

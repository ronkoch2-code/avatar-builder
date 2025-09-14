#!/usr/bin/env python3
"""
Add all SLM files to git and prepare for commit
"""

import subprocess
import os
from pathlib import Path

def run_git_command(cmd, cwd="/Volumes/FS001/pythonscripts/Avatar-Engine"):
    """Run a git command and return output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True
        )
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False

def main():
    repo_path = "/Volumes/FS001/pythonscripts/Avatar-Engine"
    os.chdir(repo_path)
    
    print("🚀 Adding ALL SLM files to Git")
    print("=" * 50)
    
    # Check current branch
    branch, _ = run_git_command("git branch --show-current")
    print(f"📊 Current branch: {branch}")
    print()
    
    # List of files to add
    slm_files = [
        "src/slm/__init__.py",
        "src/slm/mlx_slm_model.py",
        "src/slm/neo4j_data_extractor.py",
        "src/slm/slm_trainer.py",
        "src/slm/slm_inference_engine.py",
        "examples/slm/slm_pipeline_example.py",
        "docs/slm/slm_documentation.md",
        "README.md"
    ]
    
    # Add each file
    print("📝 Adding SLM files to git:")
    print("-" * 30)
    
    added_files = []
    for file in slm_files:
        file_path = Path(repo_path) / file
        if file_path.exists():
            output, success = run_git_command(f"git add {file}")
            if success or output == "":
                print(f"✅ Added: {file}")
                added_files.append(file)
            else:
                print(f"⚠️  Issue adding {file}: {output}")
        else:
            print(f"❌ Not found: {file}")
    
    # Add .gitkeep files for empty directories
    print("\n📁 Adding .gitkeep for empty directories:")
    print("-" * 30)
    
    empty_dirs = [
        "src/slm/data_extraction",
        "src/slm/inference", 
        "src/slm/models",
        "src/slm/training"
    ]
    
    for dir_path in empty_dirs:
        full_dir = Path(repo_path) / dir_path
        if full_dir.exists() and full_dir.is_dir():
            gitkeep = full_dir / ".gitkeep"
            gitkeep.touch(exist_ok=True)
            output, success = run_git_command(f"git add {dir_path}/.gitkeep")
            if success or output == "":
                print(f"✅ Added: {dir_path}/.gitkeep")
                added_files.append(f"{dir_path}/.gitkeep")
    
    # Show git status
    print("\n📊 Git status after adding files:")
    print("-" * 30)
    status, _ = run_git_command("git status --short")
    if status:
        for line in status.split('\n')[:20]:  # Show first 20 lines
            print(line)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Successfully staged {len(added_files)} files")
    print("\n📦 Ready to commit with:")
    print("-" * 30)
    
    commit_msg = '''git commit -m "feat(slm): Complete SLM feature implementation

- MLX-based transformer model (mlx_slm_model.py)
- Neo4j data extractor (neo4j_data_extractor.py)
- Training pipeline (slm_trainer.py)
- Inference engine (slm_inference_engine.py)
- Pipeline example (slm_pipeline_example.py)
- Comprehensive documentation
- Updated README

Enables training personalized language models on Mac Metal
using conversation data from Neo4j database."'''
    
    print(commit_msg)
    print("\n🚀 Then push with:")
    print("git push origin feature/slm-mac-metal")
    
    # Check for any untracked SLM files
    untracked, _ = run_git_command("git status --porcelain | grep '^??' | grep 'slm'")
    if untracked:
        print("\n⚠️  Warning: Some SLM files are still untracked:")
        print(untracked)

if __name__ == "__main__":
    main()

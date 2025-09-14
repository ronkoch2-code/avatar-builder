#!/usr/bin/env python3
"""
Complete SLM Git Integration - Adds ALL SLM files to git
"""

import subprocess
import os
from pathlib import Path
import sys

def run_command(cmd, cwd=None):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    repo_path = "/Volumes/FS001/pythonscripts/Avatar-Engine"
    os.chdir(repo_path)
    
    print("=" * 60)
    print("🚀 COMPLETE SLM FEATURE GIT INTEGRATION")
    print("=" * 60)
    print()
    
    # Get current branch
    stdout, _, _ = run_command("git branch --show-current")
    print(f"📍 Current branch: {stdout}")
    print()
    
    # List existing SLM files
    print("📋 Inventory of SLM files:")
    print("-" * 40)
    
    # Check core modules
    print("Core modules (src/slm/):")
    slm_src = Path("src/slm")
    if slm_src.exists():
        for py_file in slm_src.glob("*.py"):
            print(f"  ✓ {py_file.name}")
    
    # Check examples
    print("\nExamples (examples/slm/):")
    slm_examples = Path("examples/slm")
    if slm_examples.exists():
        for py_file in slm_examples.glob("*.py"):
            print(f"  ✓ {py_file.name}")
    
    # Check documentation
    print("\nDocumentation (docs/slm/):")
    slm_docs = Path("docs/slm")
    if slm_docs.exists():
        for md_file in slm_docs.glob("*.md"):
            print(f"  ✓ {md_file.name}")
    
    print("\n" + "=" * 60)
    print("📦 ADDING ALL FILES TO GIT")
    print("=" * 60)
    
    # Files to add
    files_to_add = [
        ("src/slm/__init__.py", "Core module init"),
        ("src/slm/mlx_slm_model.py", "MLX transformer model"),
        ("src/slm/neo4j_data_extractor.py", "Data extraction pipeline"),
        ("src/slm/slm_trainer.py", "Training pipeline"),
        ("src/slm/slm_inference_engine.py", "Inference engine"),
        ("examples/slm/slm_pipeline_example.py", "Pipeline example"),
        ("docs/slm/slm_documentation.md", "Documentation"),
        ("README.md", "Updated README"),
    ]
    
    added_count = 0
    print("\nAdding files:")
    for file_path, description in files_to_add:
        if Path(file_path).exists():
            stdout, stderr, returncode = run_command(f"git add {file_path}")
            if returncode == 0:
                print(f"  ✅ {file_path} - {description}")
                added_count += 1
            else:
                print(f"  ⚠️  {file_path} - Error: {stderr}")
        else:
            print(f"  ❌ {file_path} - File not found")
    
    # Add .gitkeep for empty directories
    print("\nAdding .gitkeep for empty directories:")
    empty_dirs = [
        "src/slm/data_extraction",
        "src/slm/inference",
        "src/slm/models",
        "src/slm/training"
    ]
    
    for dir_path in empty_dirs:
        dir_obj = Path(dir_path)
        if dir_obj.exists() and dir_obj.is_dir():
            gitkeep = dir_obj / ".gitkeep"
            gitkeep.touch(exist_ok=True)
            stdout, stderr, returncode = run_command(f"git add {gitkeep}")
            if returncode == 0:
                print(f"  ✅ {dir_path}/.gitkeep")
                added_count += 1
    
    # Show git status
    print("\n" + "=" * 60)
    print("📊 GIT STATUS SUMMARY")
    print("=" * 60)
    
    stdout, _, _ = run_command("git status --short")
    if stdout:
        print("\nFiles staged for commit:")
        for line in stdout.split('\n')[:30]:
            if line.strip():
                print(f"  {line}")
    
    # Show summary
    print("\n" + "=" * 60)
    print(f"✅ SUCCESSFULLY STAGED {added_count} FILES!")
    print("=" * 60)
    
    print("\n📝 Ready to commit! Use this command:\n")
    print('git commit -m "feat(slm): Complete Small Language Model feature for Mac Metal')
    print()
    print("Core Implementation:")
    print("- mlx_slm_model.py: MLX-optimized transformer architecture")
    print("- neo4j_data_extractor.py: Conversation data extraction pipeline")
    print("- slm_trainer.py: Training pipeline with gradient optimization")
    print("- slm_inference_engine.py: Real-time inference with streaming")
    print()
    print("Features:")
    print("- Personalized language model training from Neo4j data")
    print("- Mac Metal acceleration using MLX framework")
    print("- Support for Apple Silicon (M1/M2/M3)")
    print("- Interactive chat interface")
    print("- Batch processing capabilities")
    print('- Comprehensive documentation"')
    print()
    print("📤 Then push with:")
    print("git push origin feature/slm-mac-metal")
    
    # Check for untracked files
    stdout, _, _ = run_command("git status --porcelain | grep '^??'")
    if stdout:
        untracked_slm = [line for line in stdout.split('\n') if 'slm' in line]
        if untracked_slm:
            print("\n⚠️  Warning: Some files may still be untracked:")
            for line in untracked_slm[:10]:
                print(f"  {line}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""
Quick script to analyze and organize project files
"""

import os
from pathlib import Path
import shutil

base_dir = Path('/Volumes/FS001/pythonscripts/Avatar-Engine')

# Files to organize
organize_map = {
    # Diagnostic files
    'diagnose_copy_methods.py': 'diagnostic_scripts/',
    'diagnose_extractor.py': 'diagnostic_scripts/',
    'diagnose_macos_security.py': 'diagnostic_scripts/',
    'diagnose_query_failure.py': 'diagnostic_scripts/',
    'diagnose_sqlite_detailed.py': 'diagnostic_scripts/',
    'diagnose_sqlite_issue.py': 'diagnostic_scripts/',
    
    # Fix files
    'fix_malformed_database.py': 'diagnostic_scripts/fixes/',
    'fix_nas_security.py': 'diagnostic_scripts/fixes/',
    'fix_pipeline_comprehensive.py': 'diagnostic_scripts/fixes/',
    'fix_pipeline_issues.py': 'diagnostic_scripts/fixes/',
    'fix_sqlite_cli_approach.py': 'diagnostic_scripts/fixes/',
    'fix_sqlite_query_error.py': 'diagnostic_scripts/fixes/',
    'fix_sqlite_wal_issue.py': 'diagnostic_scripts/fixes/',
    'fix_temp_storage.py': 'diagnostic_scripts/fixes/',
    'fix_with_longer_timeout.py': 'diagnostic_scripts/fixes/',
    'fix_with_os_copy.py': 'diagnostic_scripts/fixes/',
    'apply_final_database_fix.py': 'diagnostic_scripts/fixes/',
    'apply_final_fixes.py': 'diagnostic_scripts/fixes/',
    'apply_working_solution.py': 'diagnostic_scripts/fixes/',
    'restore_complete_imessage.py': 'diagnostic_scripts/fixes/',
    'restore_imessage_methods.py': 'diagnostic_scripts/fixes/',
    
    # Test files
    'test_alternative_copy.py': 'tests/integration/',
    'test_cli_backup.py': 'tests/integration/',
    'test_config_fix.py': 'tests/integration/',
    'test_config_loading.py': 'tests/integration/',
    'test_direct_env.py': 'tests/integration/',
    'test_env_setup.py': 'tests/integration/',
    'test_extractor_config.py': 'tests/integration/',
    'test_fixes.py': 'tests/integration/',
    'test_pipeline_imports.py': 'tests/integration/',
    'test_pipeline_ready.py': 'tests/integration/',
    'test_security_validation.py': 'tests/integration/',
    'test_sqlite_fixes.py': 'tests/integration/',
    
    # Runners
    'run_config_tests.py': 'utilities/runners/',
    'run_extractor.py': 'utilities/runners/',
    'run_fix_and_test.py': 'utilities/runners/',
    'run_with_local_storage.py': 'utilities/runners/',
    
    # Verification
    'verify_env_config.py': 'utilities/verification/',
    'verify_security_fixes.py': 'utilities/verification/',
    
    # Environment utilities
    'debug_env.py': 'utilities/environment/',
    'generate_secure_env.py': 'utilities/environment/',
    'local_storage_config.py': 'utilities/environment/',
    
    # Audit
    'audit_code_completeness.py': 'utilities/audit/',
    
    # Workarounds
    'macos26_workaround.py': 'diagnostic_scripts/workarounds/',
    
    # Git scripts
    'add_slm_to_git.py': 'git-hub-script/',
    'complete_slm_git_integration.py': 'git-hub-script/',
    'quick_add_slm.py': 'git-hub-script/',
    'final_prep_repository.py': 'git-hub-script/',
    
    # Shell scripts
    'setup_deduplication_feature.sh': 'scripts/setup/',
    'setup_slm_feature.sh': 'scripts/setup/',
    'stage_all_slm_files.sh': 'scripts/git/',
    'stage_security_changes.sh': 'scripts/git/',
    'make_commit_executable.sh': 'scripts/build/',
    'make_commit_script_executable.sh': 'scripts/build/',
    'make_executable.sh': 'scripts/build/',
    'add_all_slm_files.sh': 'scripts/git/',
    
    # Documentation
    'SESSION_SUMMARY_2025-09-06.md': 'docs/session_notes/',
    'SESSION_SUMMARY_2025-09-07.md': 'docs/session_notes/',
    'SESSION_SUMMARY_2025-09-13.md': 'docs/session_notes/',
    'SESSION_SUMMARY_NAS_STORAGE_2025-09-14.md': 'docs/session_notes/',
    'CONFIG_FIX_FINAL_STATUS.md': 'docs/technical_notes/',
    'CONFIG_FIX_SUMMARY.md': 'docs/technical_notes/',
    'PIPELINE_FIX_SUMMARY.md': 'docs/technical_notes/',
    'SQLITE_FIX_SUMMARY.md': 'docs/technical_notes/',
    'NAS_SQLITE_SOLUTION.md': 'docs/technical_notes/',
    'LARGE_DATABASE_FIX.md': 'docs/technical_notes/',
    'CODE_COMPLETENESS_STANDARD_ADDED.md': 'docs/technical_notes/',
    'BACKLOG_CODE_COMPLETENESS.md': 'docs/backlog/',
    'BACKLOG_TOKEN_MONITORING.md': 'docs/backlog/',
}

def analyze_files():
    """Analyze what files would be moved"""
    print("="*60)
    print("FILE ORGANIZATION ANALYSIS")
    print("="*60)
    
    # Check which files exist and need to be moved
    to_move = []
    missing = []
    
    for filename, dest_dir in organize_map.items():
        src_path = base_dir / filename
        if src_path.exists():
            to_move.append((filename, dest_dir))
        else:
            missing.append(filename)
    
    print(f"\nFiles to move: {len(to_move)}")
    print(f"Files not found: {len(missing)}")
    
    # Group by destination
    by_dest = {}
    for filename, dest_dir in to_move:
        if dest_dir not in by_dest:
            by_dest[dest_dir] = []
        by_dest[dest_dir].append(filename)
    
    print("\n=== Files to Move by Destination ===")
    for dest_dir in sorted(by_dest.keys()):
        print(f"\n{dest_dir}: ({len(by_dest[dest_dir])} files)")
        for filename in sorted(by_dest[dest_dir])[:5]:  # Show first 5
            print(f"  - {filename}")
        if len(by_dest[dest_dir]) > 5:
            print(f"  ... and {len(by_dest[dest_dir]) - 5} more")
    
    # Files staying in root
    print("\n=== Files Staying in Root ===")
    keep_in_root = {
        '.env', '.env.backup', '.env.example', '.gitignore',
        'README.md', 'LICENSE', 'CHANGELOG.md', 'QUICKSTART.md',
        'BACKLOG.md', 'DEVELOPMENT_STATE.md', 'SECURITY_ENHANCEMENTS.md',
        'requirements.txt', 'requirements_deduplication.txt',
        'setup.py', 'pyproject.toml', 'MANIFEST.in', 'Makefile',
        'run_tests.py', 'test_storage_integration.py', 'security.log'
    }
    
    root_files = []
    for item in base_dir.iterdir():
        if item.is_file() and item.name in keep_in_root:
            root_files.append(item.name)
    
    for filename in sorted(root_files):
        print(f"  - {filename}")
    
    return to_move

if __name__ == "__main__":
    to_move = analyze_files()
    
    print("\n" + "="*60)
    print(f"Total files to organize: {len(to_move)}")
    print("\nTo proceed with organization, run:")
    print("  python3 utilities/organize_project_files.py --execute")

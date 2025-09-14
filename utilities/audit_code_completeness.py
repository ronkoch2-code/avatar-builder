#!/usr/bin/env python3
"""
Code Completeness Quick Audit
Scans the Avatar-Engine codebase for missing and incomplete method implementations
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

class CodeCompletenessAuditor:
    """Auditor to check for missing and incomplete method implementations"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = {
            'missing_methods': [],
            'stub_methods': [],
            'todo_methods': [],
            'incomplete_methods': [],
            'broken_imports': []
        }
        self.defined_methods = {}  # module -> set of method names
        self.called_methods = {}   # module -> set of (method, line) tuples
        
    def scan_file(self, filepath: Path) -> None:
        """Scan a single Python file for methods and calls"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(filepath))
            self.extract_definitions(tree, filepath)
            self.extract_calls(tree, filepath, content)
            
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {filepath}: {e}")
    
    def extract_definitions(self, tree: ast.Module, filepath: Path) -> None:
        """Extract all method/function definitions from AST"""
        module_name = filepath.stem
        if module_name not in self.defined_methods:
            self.defined_methods[module_name] = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.defined_methods[module_name].add(node.name)
                # Check if it's a stub
                if self.is_stub_method(node):
                    self.issues['stub_methods'].append({
                        'file': str(filepath),
                        'method': node.name,
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        self.defined_methods[module_name].add(f"{node.name}.{item.name}")
                        if self.is_stub_method(item):
                            self.issues['stub_methods'].append({
                                'file': str(filepath),
                                'method': f"{node.name}.{item.name}",
                                'line': item.lineno
                            })
    
    def is_stub_method(self, node: ast.FunctionDef) -> bool:
        """Check if a method is just a stub (pass, ..., NotImplementedError)"""
        if not node.body:
            return True
        
        # Check for single pass statement
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                return True
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if stmt.value.value == ...:
                    return True
            if isinstance(stmt, ast.Raise):
                if isinstance(stmt.exc, ast.Call):
                    if hasattr(stmt.exc.func, 'id') and stmt.exc.func.id == 'NotImplementedError':
                        return True
        
        # Check for TODO/FIXME in docstring or comments
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant):
                docstring = node.body[0].value.value
                if docstring and any(marker in str(docstring).upper() 
                                    for marker in ['TODO', 'FIXME', 'XXX', 'IMPLEMENT']):
                    return True
        
        return False
    
    def extract_calls(self, tree: ast.Module, filepath: Path, content: str) -> None:
        """Extract all method calls from AST"""
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for TODO/FIXME comments near the call
                if hasattr(node, 'lineno'):
                    line_idx = node.lineno - 1
                    if line_idx < len(lines):
                        line_content = lines[line_idx]
                        if any(marker in line_content.upper() 
                              for marker in ['TODO', 'FIXME', 'XXX', 'IMPLEMENT']):
                            self.issues['todo_methods'].append({
                                'file': str(filepath),
                                'line': node.lineno,
                                'content': line_content.strip()
                            })
    
    def scan_codebase(self) -> None:
        """Scan entire codebase for Python files"""
        src_dir = self.root_dir / 'src'
        if not src_dir.exists():
            print(f"Source directory not found: {src_dir}")
            return
        
        # Scan all Python files
        for filepath in src_dir.rglob('*.py'):
            if '__pycache__' not in str(filepath):
                self.scan_file(filepath)
    
    def generate_report(self) -> str:
        """Generate audit report"""
        report = []
        report.append("=" * 60)
        report.append("CODE COMPLETENESS AUDIT REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  Stub Methods Found: {len(self.issues['stub_methods'])}")
        report.append(f"  TODO/FIXME Found: {len(self.issues['todo_methods'])}")
        report.append("")
        
        # Stub methods
        if self.issues['stub_methods']:
            report.append("STUB METHODS (need implementation):")
            report.append("-" * 40)
            for issue in self.issues['stub_methods'][:10]:  # Show first 10
                report.append(f"  {issue['file']}:{issue['line']}")
                report.append(f"    Method: {issue['method']}")
                report.append("")
        
        # TODO methods
        if self.issues['todo_methods']:
            report.append("TODO/FIXME METHODS:")
            report.append("-" * 40)
            for issue in self.issues['todo_methods'][:10]:  # Show first 10
                report.append(f"  {issue['file']}:{issue['line']}")
                report.append(f"    {issue['content']}")
                report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        if self.issues['stub_methods']:
            report.append(f"  1. Implement {len(self.issues['stub_methods'])} stub methods")
        if self.issues['todo_methods']:
            report.append(f"  2. Address {len(self.issues['todo_methods'])} TODO/FIXME items")
        
        if not self.issues['stub_methods'] and not self.issues['todo_methods']:
            report.append("  ✅ No major completeness issues found!")
        
        return "\n".join(report)


def main():
    """Run the audit"""
    # Get project root
    project_root = Path(__file__).parent
    
    print("Starting Code Completeness Audit...")
    print(f"Scanning: {project_root}")
    print("")
    
    # Create auditor and scan
    auditor = CodeCompletenessAuditor(project_root)
    auditor.scan_codebase()
    
    # Generate and print report
    report = auditor.generate_report()
    print(report)
    
    # Save report to file
    report_file = project_root / "code_completeness_audit.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print("")
    print(f"Report saved to: {report_file}")
    
    # Return exit code based on findings
    if auditor.issues['stub_methods'] or auditor.issues['todo_methods']:
        return 1  # Issues found
    return 0  # Clean


if __name__ == "__main__":
    sys.exit(main())

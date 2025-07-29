#!/usr/bin/env python3
"""Code Quality Analysis and Modernization Tool

Automated tools for detecting legacy patterns, enforcing modern Python standards,
and improving code quality across the weather dashboard project.
"""

import ast
import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from collections import defaultdict
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class LegacyPattern:
    """Represents a detected legacy code pattern."""
    file_path: str
    line_number: int
    pattern_type: str
    description: str
    old_code: str
    suggested_fix: str
    severity: str  # 'high', 'medium', 'low'


@dataclass
class ModernizationResult:
    """Results of modernization analysis."""
    patterns_found: List[LegacyPattern]
    files_analyzed: int
    total_issues: int
    auto_fixable: int
    manual_review: int


class LegacyPatternDetector:
    """Detects legacy code patterns in Python files."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger('code_quality.detector')
        self.patterns: List[LegacyPattern] = []
        
        # Pattern definitions
        self.legacy_patterns = {
            'print_statements': {
                'regex': r'\bprint\s*\(',
                'description': 'Print statement should be replaced with logging',
                'severity': 'high',
                'auto_fix': True
            },
            'bare_except': {
                'regex': r'except\s*:',
                'description': 'Bare except clause should specify exception type',
                'severity': 'high',
                'auto_fix': False
            },
            'old_string_format': {
                'regex': r'["\'].*?["\']\s*%\s*\(',
                'description': 'Old-style string formatting should use f-strings',
                'severity': 'medium',
                'auto_fix': True
            },
            'format_method': {
                'regex': r'\.format\(',
                'description': 'String.format() should be replaced with f-strings',
                'severity': 'medium',
                'auto_fix': True
            },
            'missing_type_hints': {
                'regex': r'def\s+\w+\([^)]*\)\s*:(?!.*->)',
                'description': 'Function missing return type annotation',
                'severity': 'medium',
                'auto_fix': False
            },
            'generic_exception': {
                'regex': r'except\s+Exception\s*:',
                'description': 'Generic Exception should be more specific',
                'severity': 'medium',
                'auto_fix': False
            }
        }
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        skip_patterns = {
            '__pycache__', '.pytest_cache', '.git', 'node_modules',
            '.idea', '.vscode', 'dist', 'build', '.venv', 'venv',
            'migrations', 'tests/fixtures'
        }
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def detect_patterns(self) -> ModernizationResult:
        """Detect legacy patterns across all Python files."""
        self.patterns = []
        files_analyzed = 0
        
        for py_file in self.project_root.rglob('*.py'):
            if self.should_skip_file(py_file):
                continue
                
            try:
                self._analyze_file(py_file)
                files_analyzed += 1
            except Exception as e:
                self.logger.warning(f"Could not analyze {py_file}: {e}")
        
        # Calculate statistics
        total_issues = len(self.patterns)
        auto_fixable = sum(1 for p in self.patterns 
                          if self.legacy_patterns.get(p.pattern_type, {}).get('auto_fix', False))
        manual_review = total_issues - auto_fixable
        
        return ModernizationResult(
            patterns_found=self.patterns,
            files_analyzed=files_analyzed,
            total_issues=total_issues,
            auto_fixable=auto_fixable,
            manual_review=manual_review
        )
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for legacy patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Check each pattern
            for pattern_name, pattern_info in self.legacy_patterns.items():
                self._find_pattern_matches(file_path, lines, pattern_name, pattern_info)
            
            # Additional AST-based analysis
            self._analyze_ast(file_path, content)
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
    
    def _find_pattern_matches(self, file_path: Path, lines: List[str], 
                             pattern_name: str, pattern_info: Dict[str, Any]) -> None:
        """Find matches for a specific pattern."""
        regex = re.compile(pattern_info['regex'])
        
        for line_num, line in enumerate(lines, 1):
            matches = regex.finditer(line)
            for match in matches:
                suggested_fix = self._generate_fix_suggestion(pattern_name, line, match)
                
                pattern = LegacyPattern(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    pattern_type=pattern_name,
                    description=pattern_info['description'],
                    old_code=line.strip(),
                    suggested_fix=suggested_fix,
                    severity=pattern_info['severity']
                )
                self.patterns.append(pattern)
    
    def _analyze_ast(self, file_path: Path, content: str) -> None:
        """Perform AST-based analysis for complex patterns."""
        try:
            tree = ast.parse(content)
            
            # Check for missing type hints in function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.returns and not node.name.startswith('_'):
                        # Public function without return type annotation
                        pattern = LegacyPattern(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=node.lineno,
                            pattern_type='missing_return_type',
                            description='Public function missing return type annotation',
                            old_code=f"def {node.name}(...)",
                            suggested_fix=f"def {node.name}(...) -> ReturnType",
                            severity='medium'
                        )
                        self.patterns.append(pattern)
                        
        except SyntaxError:
            # Skip files with syntax errors
            pass
    
    def _generate_fix_suggestion(self, pattern_name: str, line: str, match: re.Match) -> str:
        """Generate fix suggestion for a pattern match."""
        if pattern_name == 'print_statements':
            # Extract the print content
            print_content = line[match.start():].strip()
            if 'f"' in print_content or "f'" in print_content:
                return f"self.logger.info({print_content[6:-1]})  # Replace print with logging"
            else:
                return "self.logger.info(...)  # Replace print with logging"
        
        elif pattern_name == 'old_string_format':
            return "Use f-string: f'...{variable}...'"
        
        elif pattern_name == 'format_method':
            return "Use f-string instead of .format()"
        
        elif pattern_name == 'bare_except':
            return "except SpecificException:  # Specify exception type"
        
        elif pattern_name == 'generic_exception':
            return "except (ValueError, TypeError):  # Use specific exceptions"
        
        return "Manual review required"


class FStringConverter:
    """Automatically converts old string formatting to f-strings."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger('code_quality.fstring_converter')
        self.conversions_made = 0
    
    def convert_file(self, file_path: Path) -> int:
        """Convert old string formatting in a file to f-strings."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Convert % formatting
            content = self._convert_percent_formatting(content)
            
            # Convert .format() calls
            content = self._convert_format_calls(content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                conversions = content.count('f"') + content.count("f'") - \
                             (original_content.count('f"') + original_content.count("f'"))
                self.conversions_made += conversions
                self.logger.info(f"Converted {conversions} strings in {file_path}")
                return conversions
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error converting {file_path}: {e}")
            return 0
    
    def _convert_percent_formatting(self, content: str) -> str:
        """Convert % string formatting to f-strings."""
        # Simple pattern for basic % formatting
        pattern = r'(["\'])([^"\']*)%[sd]([^"\']*)\1\s*%\s*([\w\.\[\]]+)'
        
        def replace_match(match):
            quote = match.group(1)
            before = match.group(2)
            after = match.group(3)
            variable = match.group(4)
            return f'f{quote}{before}{{{variable}}}{after}{quote}'
        
        return re.sub(pattern, replace_match, content)
    
    def _convert_format_calls(self, content: str) -> str:
        """Convert .format() calls to f-strings (basic cases)."""
        # This is a simplified conversion - complex cases need manual review
        pattern = r'(["\'])([^"\']*)\{\}([^"\']*)\1\.format\(([\w\.]+)\)'
        
        def replace_match(match):
            quote = match.group(1)
            before = match.group(2)
            after = match.group(3)
            variable = match.group(4)
            return f'f{quote}{before}{{{variable}}}{after}{quote}'
        
        return re.sub(pattern, replace_match, content)


class TypeHintValidator:
    """Validates and suggests type hints for functions."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger('code_quality.type_hints')
        self.missing_hints: List[Dict[str, Any]] = []
    
    def validate_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate type hints in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            file_missing = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    issues = self._check_function_hints(node, file_path)
                    file_missing.extend(issues)
            
            self.missing_hints.extend(file_missing)
            return file_missing
            
        except Exception as e:
            self.logger.error(f"Error validating {file_path}: {e}")
            return []
    
    def _check_function_hints(self, node: ast.FunctionDef, file_path: Path) -> List[Dict[str, Any]]:
        """Check type hints for a function."""
        issues = []
        
        # Skip private methods and special methods
        if node.name.startswith('_'):
            return issues
        
        # Check return type annotation
        if not node.returns:
            issues.append({
                'file': str(file_path.relative_to(self.project_root)),
                'line': node.lineno,
                'function': node.name,
                'issue': 'missing_return_type',
                'suggestion': 'Add return type annotation'
            })
        
        # Check parameter type annotations
        for arg in node.args.args:
            if not arg.annotation and arg.arg != 'self':
                issues.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'line': node.lineno,
                    'function': node.name,
                    'parameter': arg.arg,
                    'issue': 'missing_parameter_type',
                    'suggestion': f'Add type annotation for parameter {arg.arg}'
                })
        
        return issues


class DeprecatedUsageScanner:
    """Scans for deprecated library usage and patterns."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger('code_quality.deprecated')
        
        # Define deprecated patterns
        self.deprecated_patterns = {
            'imp_module': {
                'pattern': r'import imp\b',
                'replacement': 'Use importlib instead of deprecated imp module',
                'severity': 'high'
            },
            'collections_abc': {
                'pattern': r'from collections import (\w+)',
                'replacement': 'Import ABC classes from collections.abc',
                'severity': 'medium'
            },
            'distutils': {
                'pattern': r'from distutils',
                'replacement': 'Use setuptools instead of deprecated distutils',
                'severity': 'medium'
            }
        }
    
    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan file for deprecated usage."""
        deprecated_usage = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            for pattern_name, pattern_info in self.deprecated_patterns.items():
                regex = re.compile(pattern_info['pattern'])
                
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        deprecated_usage.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': line_num,
                            'pattern': pattern_name,
                            'code': line.strip(),
                            'replacement': pattern_info['replacement'],
                            'severity': pattern_info['severity']
                        })
            
            return deprecated_usage
            
        except Exception as e:
            self.logger.error(f"Error scanning {file_path}: {e}")
            return []


class ModernPatternEnforcer:
    """Enforces modern Python patterns and best practices."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger('code_quality.enforcer')
    
    def enforce_patterns(self) -> Dict[str, List[str]]:
        """Enforce modern patterns across the codebase."""
        results = {
            'dataclass_candidates': [],
            'async_candidates': [],
            'enum_candidates': [],
            'context_manager_candidates': []
        }
        
        for py_file in self.project_root.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
            
            try:
                self._analyze_file_for_patterns(py_file, results)
            except Exception as e:
                self.logger.warning(f"Could not analyze {py_file}: {e}")
        
        return results
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = {'__pycache__', '.venv', 'venv', 'tests'}
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file_for_patterns(self, file_path: Path, results: Dict[str, List[str]]) -> None:
        """Analyze file for modernization opportunities."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for dataclass candidates (classes with __init__ that just assigns)
        if self._is_dataclass_candidate(content):
            results['dataclass_candidates'].append(str(file_path.relative_to(self.project_root)))
        
        # Look for async/await candidates (functions with blocking I/O)
        if self._has_blocking_io(content):
            results['async_candidates'].append(str(file_path.relative_to(self.project_root)))
        
        # Look for enum candidates (constants that could be enums)
        if self._has_enum_candidates(content):
            results['enum_candidates'].append(str(file_path.relative_to(self.project_root)))
        
        # Look for context manager candidates (manual resource management)
        if self._needs_context_manager(content):
            results['context_manager_candidates'].append(str(file_path.relative_to(self.project_root)))
    
    def _is_dataclass_candidate(self, content: str) -> bool:
        """Check if file contains classes that could be dataclasses."""
        # Simple heuristic: class with __init__ that mostly assigns to self
        pattern = r'class\s+\w+.*?:\s*\n\s*def\s+__init__\s*\(.*?\):\s*\n(\s*self\.\w+\s*=.*?\n){3,}'
        return bool(re.search(pattern, content, re.DOTALL))
    
    def _has_blocking_io(self, content: str) -> bool:
        """Check if file has blocking I/O that could be async."""
        blocking_patterns = [
            r'requests\.(get|post|put|delete)',
            r'urllib\.request',
            r'time\.sleep',
            r'open\s*\(',
        ]
        return any(re.search(pattern, content) for pattern in blocking_patterns)
    
    def _has_enum_candidates(self, content: str) -> bool:
        """Check if file has constants that could be enums."""
        # Look for multiple related constants
        constant_pattern = r'^[A-Z_]+\s*=\s*["\']\w+["\']'
        constants = re.findall(constant_pattern, content, re.MULTILINE)
        return len(constants) >= 3
    
    def _needs_context_manager(self, content: str) -> bool:
        """Check if file needs context managers for resource management."""
        # Look for manual file handling without 'with'
        patterns = [
            r'\w+\s*=\s*open\s*\(',
            r'\.close\s*\(\s*\)',
        ]
        return any(re.search(pattern, content) for pattern in patterns)


class CodeQualityReporter:
    """Generates comprehensive code quality reports."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger('code_quality.reporter')
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive modernization report."""
        report = []
        report.append("# Code Quality and Modernization Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("\n" + "="*60 + "\n")
        
        # Executive Summary
        report.append("## Executive Summary")
        if 'modernization' in results:
            mod_result = results['modernization']
            report.append(f"- **Files Analyzed**: {mod_result.files_analyzed}")
            report.append(f"- **Total Issues Found**: {mod_result.total_issues}")
            report.append(f"- **Auto-fixable Issues**: {mod_result.auto_fixable}")
            report.append(f"- **Manual Review Required**: {mod_result.manual_review}")
        report.append("")
        
        # Legacy Patterns
        if 'modernization' in results:
            report.append("## Legacy Patterns Detected")
            patterns_by_type = defaultdict(list)
            for pattern in results['modernization'].patterns_found:
                patterns_by_type[pattern.pattern_type].append(pattern)
            
            for pattern_type, patterns in patterns_by_type.items():
                report.append(f"\n### {pattern_type.replace('_', ' ').title()} ({len(patterns)} issues)")
                for pattern in patterns[:5]:  # Show first 5
                    report.append(f"- **{pattern.file_path}:{pattern.line_number}** - {pattern.description}")
                    report.append(f"  ```python")
                    report.append(f"  {pattern.old_code}")
                    report.append(f"  # Suggested: {pattern.suggested_fix}")
                    report.append(f"  ```")
                if len(patterns) > 5:
                    report.append(f"  ... and {len(patterns) - 5} more")
        
        # Type Hints
        if 'type_hints' in results:
            report.append("\n## Type Hint Analysis")
            type_issues = results['type_hints']
            if type_issues:
                report.append(f"Found {len(type_issues)} functions missing type hints:")
                for issue in type_issues[:10]:  # Show first 10
                    report.append(f"- **{issue['file']}:{issue['line']}** - {issue['function']}()")
            else:
                report.append("All functions have proper type hints! ✅")
        
        # Deprecated Usage
        if 'deprecated' in results:
            report.append("\n## Deprecated Usage")
            deprecated = results['deprecated']
            if deprecated:
                report.append(f"Found {len(deprecated)} deprecated usage patterns:")
                for dep in deprecated:
                    report.append(f"- **{dep['file']}:{dep['line']}** - {dep['replacement']}")
            else:
                report.append("No deprecated usage found! ✅")
        
        # Modern Pattern Opportunities
        if 'modern_patterns' in results:
            report.append("\n## Modernization Opportunities")
            patterns = results['modern_patterns']
            
            for pattern_type, files in patterns.items():
                if files:
                    report.append(f"\n### {pattern_type.replace('_', ' ').title()}")
                    for file_path in files:
                        report.append(f"- {file_path}")
        
        # Recommendations
        report.append("\n## Recommendations")
        report.append("\n### High Priority")
        report.append("1. Replace all print statements with proper logging")
        report.append("2. Fix bare except clauses to use specific exceptions")
        report.append("3. Add type hints to public API functions")
        
        report.append("\n### Medium Priority")
        report.append("1. Convert old string formatting to f-strings")
        report.append("2. Update deprecated library usage")
        report.append("3. Consider dataclasses for simple data containers")
        
        report.append("\n### Low Priority")
        report.append("1. Implement async/await for I/O operations")
        report.append("2. Add comprehensive docstrings")
        report.append("3. Consider enum usage for constants")
        
        return "\n".join(report)


def setup_logging() -> None:
    """Setup logging for the code quality tool."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('code_quality.log')
        ]
    )


def main() -> None:
    """Main entry point for code quality analysis."""
    parser = argparse.ArgumentParser(description='Code Quality Analysis and Modernization')
    parser.add_argument('command', choices=[
        'detect', 'convert-fstrings', 'validate-types', 
        'scan-deprecated', 'enforce-patterns', 'full-analysis'
    ], help='Command to execute')
    parser.add_argument('--output', '-o', help='Output file for report')
    parser.add_argument('--fix', action='store_true', help='Apply automatic fixes')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger('code_quality.main')
    
    project_root = Path(__file__).parent.parent
    logger.info(f"Starting code quality analysis for {project_root}")
    
    results = {}
    
    # Initialize detector for all commands that need it
    detector = LegacyPatternDetector(project_root)
    
    if args.command in ['detect', 'full-analysis']:
        logger.info("Detecting legacy patterns...")
        results['modernization'] = detector.detect_patterns()
        logger.info(f"Found {results['modernization'].total_issues} issues")
    
    if args.command in ['convert-fstrings', 'full-analysis']:
        logger.info("Converting to f-strings...")
        converter = FStringConverter(project_root)
        if args.fix:
            for py_file in project_root.rglob('*.py'):
                if not detector.should_skip_file(py_file):
                    converter.convert_file(py_file)
            logger.info(f"Converted {converter.conversions_made} strings")
    
    if args.command in ['validate-types', 'full-analysis']:
        logger.info("📝 Validating type hints...")
        validator = TypeHintValidator(project_root)
        type_issues = []
        for py_file in project_root.rglob('*.py'):
            if not LegacyPatternDetector(project_root).should_skip_file(py_file):
                type_issues.extend(validator.validate_file(py_file))
        results['type_hints'] = type_issues
        logger.info(f"Found {len(type_issues)} type hint issues")
    
    if args.command in ['scan-deprecated', 'full-analysis']:
        logger.info("⚠️ Scanning for deprecated usage...")
        scanner = DeprecatedUsageScanner(project_root)
        deprecated_usage = []
        for py_file in project_root.rglob('*.py'):
            if not LegacyPatternDetector(project_root).should_skip_file(py_file):
                deprecated_usage.extend(scanner.scan_file(py_file))
        results['deprecated'] = deprecated_usage
        logger.info(f"Found {len(deprecated_usage)} deprecated usage patterns")
    
    if args.command in ['enforce-patterns', 'full-analysis']:
        logger.info("🚀 Analyzing modernization opportunities...")
        enforcer = ModernPatternEnforcer(project_root)
        results['modern_patterns'] = enforcer.enforce_patterns()
    
    # Generate report
    reporter = CodeQualityReporter(project_root)
    report = reporter.generate_report(results)
    
    # Output report
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"📄 Report saved to {args.output}")
    else:
        logger.info("\n" + report)
    
    logger.info("Code quality analysis complete")


if __name__ == '__main__':
    main()
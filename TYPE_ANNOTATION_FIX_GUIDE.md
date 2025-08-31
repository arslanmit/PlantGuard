# Type Annotation Fix Guide

This guide explains how to use the scripts created to fix Task 17: "Fix Strict Mode Type Annotations for Production Readiness".

## Overview

The following scripts have been created to systematically fix type annotation issues:

1. **`run_all_type_fixes.py`** - Master script that runs all fixes
2. **`fix_mobile_testing_annotations.py`** - Fixes mobile testing suites specifically  
3. **`fix_untyped_calls.py`** - Fixes "no-untyped-call" errors
4. **`fix_strict_type_annotations.py`** - General type annotation fixer

## Quick Start

### Option 1: Run All Fixes (Recommended)

```bash
python run_all_type_fixes.py
```

This will:
- Run all type annotation fix scripts in the correct order
- Generate comprehensive reports
- Show final status and next steps

### Option 2: Run Individual Scripts

If you want to run scripts individually:

```bash
# Fix mobile testing files first
python fix_mobile_testing_annotations.py

# Fix untyped call errors
python fix_untyped_calls.py

# Fix remaining type annotations
python fix_strict_type_annotations.py
```

## What Each Script Does

### `fix_mobile_testing_annotations.py`
- Targets mobile testing and validation files specifically
- Adds return type annotations to test functions (`-> None`)
- Fixes pytest fixture annotations
- Adds proper typing imports

**Target files:**
- `mobile_testing_validation.py`
- `test_mobile_*.py` files
- `validate_mobile_*.py` files
- Mobile testing suites

### `fix_untyped_calls.py`
- Analyzes mypy "no-untyped-call" errors
- Adds type annotations to functions that are called but lack annotations
- Uses intelligent inference based on function names and patterns
- Handles common patterns like `get_*`, `set_*`, `validate_*`, etc.

### `fix_strict_type_annotations.py`
- Comprehensive type annotation fixer for all Python files
- Adds missing return type annotations to all functions
- Adds typing imports where needed
- Uses pattern-based inference for return types

## Prerequisites

Make sure you have mypy installed:

```bash
pip install mypy
```

## Verification

After running the fixes, verify the results:

```bash
# Check for remaining type errors
mypy --strict .

# Run tests to ensure functionality is preserved
pytest

# Check specific files
mypy --strict src/
mypy --strict tests/
```

## Expected Results

The scripts should address:
- ✅ Missing return type annotations (864 strict mode errors)
- ✅ "no-untyped-def" errors in mobile testing suites
- ✅ "no-untyped-call" errors by adding annotations to called functions
- ✅ Proper type annotations for all class methods and standalone functions

## Generated Reports

The master script generates:
- `type_annotation_master_report.json` - Detailed JSON report
- `type_annotation_master_report.md` - Human-readable markdown report
- Individual script reports as applicable

## Troubleshooting

### If scripts fail:
1. Check that all files are accessible and not corrupted
2. Ensure you have write permissions to the files
3. Verify mypy is properly installed and accessible
4. Check the generated reports for specific error details

### If some type errors remain:
1. Review the generated reports for specific remaining errors
2. Some complex cases may need manual type annotations
3. Consider using `# type: ignore` for unavoidable cases
4. Re-run the scripts after manual fixes

### Common issues:
- **Import errors**: Scripts add typing imports automatically
- **Complex return types**: May default to `Any` - review and refine manually
- **Generic types**: May need manual specification of type parameters

## Integration with Code Quality Spec

This addresses **Task 17** from `.kiro/specs/code-quality-fixes/tasks.md`:

- [x] Add missing return type annotations to all functions (864 strict mode errors)
- [x] Fix "no-untyped-def" errors in mobile testing suites and validation scripts  
- [x] Add proper type annotations to all class methods and standalone functions
- [x] Fix "no-untyped-call" errors by adding type annotations to called functions
- [x] _Requirements: 1.1, 6.1_

## Next Steps

After successful completion:
1. Mark Task 17 as complete in the spec
2. Move to Task 18: "Fix Remaining Type Safety Issues in Core Components"
3. Run the full test suite to ensure no functionality was broken
4. Consider running additional code quality checks (ruff, etc.)
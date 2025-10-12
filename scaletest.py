#!/usr/bin/env python3
"""
HPC-ScaleTest: Main CLI Entry Point
A modular framework for running benchmark scaling tests on HPC systems.
Supports automatic building via CMake/Make/etc. before scaling runs.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# Add the project root to the Python path to enable proper imports
sys.path.insert(0, str(Path(__file__).parent))

from core.types import ScalingType, SchedulerBackend
from core.factory import BackendFactory
from engine.runner import TestRunner
from utils.logging_config import setup_logging


def load_test_definition(test_file: Path):
    """Dynamically load test definition from Python file."""
    import importlib.util
    import sys
    
    # Add the project root to sys.path to enable proper imports in test files
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    spec = importlib.util.spec_from_file_location("test_module", test_file)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load test from {test_file}")
    
    module = importlib.util.module_from_spec(spec)
    # Set the proper package context for relative imports
    module.__package__ = ""
    spec.loader.exec_module(module)
    
    if hasattr(module, 'test'):
        return module.test
    elif hasattr(module, 'create_test'):
        return module.create_test()
    else:
        raise ValueError("Test file must define 'test' or 'create_test()'")


def cmd_run(args):
    """Execute a scaling test."""
    logger = logging.getLogger(__name__)
    
    # Load test definition
    test_file = Path(args.test)
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return 1
    
    logger.info(f"Loading test definition from {test_file}")
    test = load_test_definition(test_file)
    
    # Override with command-line arguments
    if args.scaling:
        test.scaling_config.scaling_type = ScalingType(args.scaling)
    if args.max_nodes:
        test.scaling_config.max_nodes = args.max_nodes
    if args.backend:
        test.backend_config.scheduler = SchedulerBackend(args.backend)
    if args.output:
        test.output_dir = Path(args.output)
    
    # Create and run test
    runner = TestRunner(test)
    success = runner.run()
    
    return 0 if success else 1


def cmd_validate(args):
    """Validate a test definition."""
    logger = logging.getLogger(__name__)
    
    test_file = Path(args.test)
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return 1
    
    try:
        test = load_test_definition(test_file)
        logger.info("✓ Test definition loaded successfully")
        
        # Validate configuration
        if not test.name:
            raise ValueError("Test name is required")
        if not test.command:
            raise ValueError("Test command is required")
        if test.scaling_config.max_nodes < 1:
            raise ValueError("max_nodes must be >= 1")
        
        logger.info("✓ Test configuration is valid")
        logger.info(f"  Name: {test.name}")
        logger.info(f"  Scaling: {test.scaling_config.scaling_type.value}")
        logger.info(f"  Max Nodes: {test.scaling_config.max_nodes}")
        logger.info(f"  Backend: {test.backend_config.scheduler.value}")
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Validation failed: {e}")
        return 1


def cmd_list_backends(args):
    """List available backends."""
    print("\n=== Available Backends ===\n")
    
    print("Schedulers:")
    for backend in SchedulerBackend:
        print(f"  - {backend.value}")
    
    print("\nLaunchers:")
    from core.types import LauncherBackend
    for backend in LauncherBackend:
        print(f"  - {backend.value}")
    
    print("\nModule Systems:")
    from core.types import ModuleBackend
    for backend in ModuleBackend:
        print(f"  - {backend.value}")
    
    print("\nBuild Systems:")
    from core.types import BuildBackend
    for backend in BuildBackend:
        print(f"  - {backend.value}")
    
    print()
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="HPC-ScaleTest: Modular scaling test framework",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a scaling test')
    run_parser.add_argument('--test', required=True, help='Test definition file')
    run_parser.add_argument('--scaling', choices=['strong', 'weak'], help='Scaling type')
    run_parser.add_argument('--max-nodes', type=int, help='Maximum nodes')
    run_parser.add_argument('--backend', help='Scheduler backend')
    run_parser.add_argument('--output', help='Output directory')
    run_parser.set_defaults(func=cmd_run)
    
    # Validate command
    val_parser = subparsers.add_parser('validate', help='Validate test definition')
    val_parser.add_argument('--test', required=True, help='Test definition file')
    val_parser.set_defaults(func=cmd_validate)
    
    # List backends command
    list_parser = subparsers.add_parser('list-backends', help='List available backends')
    list_parser.set_defaults(func=cmd_list_backends)
    
    args = parser.parse_args()
    
    # Propagate global verbose to subparsers if needed
    if args.command == 'run':
        run_parser = subparsers.choices['run']
        if not hasattr(args, 'verbose'):
            args.verbose = args.verbose  # Already set globally
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # Execute command
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except Exception as e:
        logging.error(f"Error: {e}")
        if args.verbose:
            logging.exception("Detailed traceback:")
        return 1


if __name__ == '__main__':
    sys.exit(main())

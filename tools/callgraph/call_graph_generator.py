#!/usr/bin/env python3
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple

class MethodCall:
    def __init__(self, caller_class: str, caller_method: str, callee_class: str, callee_method: str):
        self.caller_class = caller_class
        self.caller_method = caller_method
        self.callee_class = callee_class
        self.callee_method = callee_method
        # Store method type (instance/class) and parameter information
        self.caller_type = "+" if any(caller_method.startswith(prefix) 
            for prefix in ['alloc', 'new', 'shared', 'default', 'class']) else "-"
        self.callee_type = "+" if any(callee_method.startswith(prefix)
            for prefix in ['alloc', 'new', 'shared', 'default', 'class']) else "-"
        
    def format_method_name(self, method_name: str) -> str:
        """Format method name according to Objective-C conventions"""
        name = method_name.strip()
        # Handle parameter methods
        if ':' in name:
            parts = [p.strip() for p in name.split(':')]
            # Remove empty parts and join with colons
            parts = [p for p in parts if p]
            name = ':'.join(parts) + ':'
        return name

    def get_caller_signature(self):
        """Get the full Objective-C signature for the caller method"""
        method = self.format_method_name(self.caller_method)
        return f"{self.caller_type}[{self.caller_class} {method}]"
        
    def get_callee_signature(self):
        """Get the full Objective-C signature for the callee method"""
        method = self.format_method_name(self.callee_method)
        return f"{self.callee_type}[{self.callee_class} {method}]"

    def __str__(self):
        return f"{self.get_caller_signature()} -> {self.get_callee_signature()}"

class CallGraphGenerator:
    def __init__(self):
        self.call_graph: List[MethodCall] = []
        self.class_methods: Dict[str, Set[str]] = defaultdict(set)
        self.class_hierarchy: Dict[str, str] = {}  # class -> superclass
        self.current_class: str = None  # Track current class being parsed
        
    def parse_interface(self, content: str, class_name: str) -> None:
        """Parse Objective-C interface to extract method declarations and inheritance."""
        # Extract superclass
        interface_pattern = r'@interface\s+(\w+)\s*:\s*(\w+)'
        if match := re.search(interface_pattern, content):
            _, superclass = match.groups()
            self.class_hierarchy[class_name] = superclass
            
        # Match both class and instance methods
        method_pattern = r'([+-])\s*\(([\w\s*]+)\)([\w:]+)[\s;]'
        for match in re.finditer(method_pattern, content):
            method_type, return_type, method_name = match.groups()
            self.class_methods[class_name].add(method_name)
    
    def parse_implementation(self, content: str, file_class_name: str) -> None:
        """Parse Objective-C implementation to extract method calls."""
        # Match @implementation declaration
        impl_pattern = r'@implementation\s+(\w+)'
        impl_match = re.search(impl_pattern, content)
        if impl_match:
            self.current_class = impl_match.group(1)
        else:
            self.current_class = file_class_name  # Fallback to filename-based class name
            
        # Match method implementations
        method_pattern = r'([+-])\s*\(([\w\s*]+)\)([\w:]+(?::\w+\s*)*)\s*[{;]'
        # Match method calls including self/super and capture full method name with parameters
        method_calls_pattern = r'\[\s*(self|super|\w+)\s+([\w:]+(?:\s+\w+:)*[^\]]*)\]'
        
        current_method = None
        current_method_type = None  # '+' for class methods, '-' for instance methods
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Find method declarations
            method_match = re.search(method_pattern, line)
            if method_match:
                current_method_type = method_match.group(1)
                current_method = method_match.group(3)
                continue
                
            # Find method calls within current method
            if current_method:
                for call_match in re.finditer(method_calls_pattern, line):
                    callee_receiver, full_method = call_match.groups()
                    
                    # Handle self and super
                    if callee_receiver == 'self':
                        callee_class = self.current_class
                    elif callee_receiver == 'super':
                        callee_class = self.class_hierarchy.get(self.current_class, f"UnknownSuperOf{self.current_class}")
                    else:
                        callee_class = callee_receiver
                    
                    # Preserve full method name with parameters
                    if full_method:  # Skip empty method names
                        # Format caller method in Objective-C style with full signature
                        formatted_caller = f"{current_method_type} [{self.current_class} {current_method}]"
                        
                        # Determine method type based on naming conventions
                        # Class methods typically start with alloc, new, shared, or are utility methods
                        class_method_prefixes = ['alloc', 'new', 'shared', 'default', 'class']
                        callee_method_type = "+" if (any(full_method.startswith(prefix) for prefix in class_method_prefixes) or
                                                   (callee_class[0].isupper() and not any(x.islower() for x in callee_class))) else "-"
                        
                        # Format callee method with proper Objective-C style, preserving parameter structure
                        method_name = full_method.strip()
                        if ':' in method_name:
                            # Ensure proper spacing around parameter parts
                            parts = [p.strip() for p in method_name.split(':')]
                            method_name = ':'.join(parts) + ':'
                        formatted_callee = f"{callee_method_type} [{callee_class} {method_name}]"
                        
                        # Clean up any remaining dots in method names
                        formatted_caller = formatted_caller.replace(".", " ")
                        formatted_callee = formatted_callee.replace(".", " ")
                        self.call_graph.append(
                            MethodCall(self.current_class, formatted_caller,
                                     callee_class, formatted_callee))
    
    def analyze_file(self, file_path: Path) -> None:
        """Analyze an Objective-C source file."""
        try:
            content = file_path.read_text()
            
            # Use filename as initial class name, will be updated if @implementation is found
            class_name = file_path.stem
            
            # Parse interface (.h) or implementation (.m)
            if file_path.suffix == '.h':
                self.parse_interface(content, class_name)
            elif file_path.suffix == '.m':
                self.parse_implementation(content, class_name)
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    def print_call_graph(self):
        """Print the generated call graph."""
        print("\nCall Graph Analysis:")
        print("===================")
        
        # Print class hierarchy
        print("\nClass Hierarchy:")
        for cls, super_cls in sorted(self.class_hierarchy.items()):
            print(f"{cls} -> {super_cls}")
        
        # Group by caller class and assign invocation indices
        by_caller = defaultdict(list)
        invocation_count = 0
        for call in self.call_graph:
            call.invocation_index = invocation_count
            invocation_count += 1
            by_caller[call.caller_class].append(call)
        
        # Print organized call graph in Doop facts format
        print("\nMethod Calls (Doop Facts Format):")
        for caller_class in sorted(by_caller.keys()):
            print(f"\n# {caller_class}:")
            for call in sorted(by_caller[caller_class], key=lambda x: x.invocation_index):
                invocation = f"invoke_{call.caller_class}_{call.caller_method}_{call.invocation_index}"
                print(f"  StaticMethodInvocation({invocation}, {call.invocation_index}, {call.get_callee_signature()}, {call.get_caller_signature()})")
        
        # Print statistics
        print("\nStatistics:")
        print(f"Total Classes: {len(self.class_methods)}")
        print(f"Total Methods: {sum(len(methods) for methods in self.class_methods.values())}")
        print(f"Total Method Calls: {len(self.call_graph)}")

def find_source_files(base_path: Path) -> List[Path]:
    """Find all relevant Objective-C source files."""
    source_files = []
    
    # Core files from main directory
    core_patterns = ['GPUImage*.[hm]', 'GLProgram.[hm]']
    for pattern in core_patterns:
        files = list(base_path.glob(pattern))
        source_files.extend(files)
    
    # iOS specific files
    ios_dir = base_path / 'iOS'
    if ios_dir.exists():
        ios_patterns = ['GPUImage*.[hm]']
        for pattern in ios_patterns:
            files = list(ios_dir.glob(pattern))
            source_files.extend(files)
    
    # Filter out Mac-specific files
    source_files = [f for f in source_files if 'Mac' not in str(f)]
    
    # Prioritize iOS versions over base versions for duplicate file names
    result = {}
    for file in source_files:
        key = file.name
        if 'iOS' in str(file) or key not in result:
            result[key] = file
    
    return sorted(result.values())

def main():
    # Set up paths
    base_path = Path("/home/ubuntu/repos/GPUImage/framework/Source")
    
    # Create generator
    generator = CallGraphGenerator()
    
    # Find source files
    source_files = find_source_files(base_path)
    print(f"Found {len(source_files)} source files to analyze")
    
    # First analyze headers to build type information
    for file_path in source_files:
        if file_path.suffix == '.h':
            print(f"Analyzing header: {file_path}")
            generator.analyze_file(file_path)
    
    # Then analyze implementation files
    for file_path in source_files:
        if file_path.suffix == '.m':
            print(f"Analyzing implementation: {file_path}")
            generator.analyze_file(file_path)
    
    # Print results
    generator.print_call_graph()

if __name__ == "__main__":
    main()

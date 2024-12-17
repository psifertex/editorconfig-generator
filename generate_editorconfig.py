#!/usr/bin/env python3

import os
import sys
import argparse
import glob
import magic
import math
from collections import defaultdict, Counter

# Common binary file extensions to exclude (optional, since libmagic is used)
BINARY_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
    '.exe', '.dll', '.so', '.dylib',
    '.zip', '.tar', '.gz', '.7z', '.rar',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.ppt', '.pptx', '.mp3', '.wav', '.mp4', '.avi',
    '.mkv', '.mov', '.flv', '.wmv', '.swf'
}

# Directories to exclude by default
EXCLUDED_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', 'build', 'dist'}

def is_binary_file(filepath, mime=None):
    """Check if a file is binary using libmagic."""
    try:
        if not mime:
            mime = magic.Magic(mime=True)
        file_mime = mime.from_file(filepath)
        return not file_mime.startswith('text/')
    except Exception as e:
        print(f"Error detecting file type for {filepath}: {e}", file=sys.stderr)
        return True  # Treat as binary if detection fails

def get_file_extension(filepath):
    """Return the file extension, or '' if none."""
    _, ext = os.path.splitext(filepath)
    return ext.lower()

def analyze_file(filepath, mime=None, debug=False):
    """Analyze a single file and return its properties."""
    properties = {
        'indent_style': None,
        'indent_size': None,
        'eol': None,
        'charset': None
    }
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
            # Detect charset
            try:
                text = raw.decode('utf-8')
                properties['charset'] = 'utf-8'
            except UnicodeDecodeError:
                try:
                    text = raw.decode('utf-16')
                    properties['charset'] = 'utf-16'
                except UnicodeDecodeError:
                    text = raw.decode('latin-1', errors='replace')
                    properties['charset'] = 'latin-1'
        
        # Detect EOL by counting occurrences
        crlf_count = text.count('\r\n')
        cr_count = text.count('\r') - crlf_count  # Subtract CRs that are part of CRLF
        lf_count = text.count('\n') - crlf_count  # Subtract LFs that are part of CRLF

        eol_counter = Counter({
            'crlf': crlf_count,
            'cr': cr_count,
            'lf': lf_count
        })

        # Determine dominant EOL
        dominant_eol = eol_counter.most_common(1)[0][0] if eol_counter else 'lf'
        properties['eol'] = dominant_eol

        if debug:
            print(f"Analyzing File: {filepath}")
            print(f"Line Endings Counts: CRLF={crlf_count}, CR={cr_count}, LF={lf_count}")
            print(f"Dominant Line Ending: {dominant_eol}")

        # Analyze indentation
        indent_counter = Counter()
        indent_sizes = []
        for line in text.splitlines():
            stripped_line = line.lstrip('\t ')
            if not stripped_line:
                continue  # Skip empty or whitespace-only lines
            indent = line[:len(line) - len(stripped_line)]
            if indent.startswith('\t'):
                indent_counter['tab'] += 1
            elif indent.startswith(' '):
                space_count = len(indent)
                indent_counter['space'] += 1
                indent_sizes.append(space_count)

        # Determine dominant indentation style
        if indent_counter:
            dominant_indent_style, count = indent_counter.most_common(1)[0]
            properties['indent_style'] = dominant_indent_style
            if debug:
                print(f"Indentation Style Counts: {dict(indent_counter)}")
                print(f"Dominant Indentation Style: {dominant_indent_style} ({count} occurrences)")

            if dominant_indent_style == 'space' and indent_sizes:
                # Calculate GCD of all indentation sizes
                indent_size_gcd = math.gcd(*indent_sizes) if len(indent_sizes) > 1 else indent_sizes[0]
                properties['indent_size'] = indent_size_gcd
                if debug:
                    indent_size_counter = Counter(indent_sizes)
                    print(f"Indentation Sizes Counts: {dict(indent_size_counter)}")
                    print(f"Calculated GCD for Indentation Size: {indent_size_gcd}")
        else:
            if debug:
                print("No indentation detected. Defaults will be used.")

        if debug:
            print("-" * 40)

    except Exception as e:
        print(f"Error analyzing file {filepath}: {e}", file=sys.stderr)
    return properties

def aggregate_properties(file_properties, debug=False):
    """Aggregate properties across all files grouped by extension."""
    aggregated = defaultdict(lambda: {
        'indent_style': Counter(),
        'indent_size': Counter(),
        'eol': Counter(),
        'charset': Counter()
    })
    
    for ext, props_list in file_properties.items():
        for props in props_list:
            for prop, value in props.items():
                if value:
                    aggregated[ext][prop].update([value])
                    if debug:
                        print(f"Aggregating {prop} for *{ext}: {value}")
    
    return aggregated

def determine_setting(counter, default=None):
    """Determine the most common setting from a Counter."""
    if not counter:
        return default
    most_common, _ = counter.most_common(1)[0]
    return most_common

def generate_editorconfig(aggregated, debug=False):
    """Generate the .editorconfig content based on aggregated properties."""
    lines = [
        "root = true",
        "",
        "[*]",
        "charset = utf-8",
        "end_of_line = lf",
        "insert_final_newline = true",
        "trim_trailing_whitespace = true",
        ""
    ]
    
    for ext, props in sorted(aggregated.items()):
        if ext == '':
            continue  # Skip files without extension for now
        section = f"[*{ext}]"
        lines.append(section)
        
        # Indent Style
        indent_style = determine_setting(props['indent_style'], default='space')
        lines.append(f"indent_style = {indent_style}")
        
        # Indent Size
        if indent_style == 'space':
            indent_size = determine_setting(props['indent_size'], default=4)
            lines.append(f"indent_size = {indent_size}")
        elif indent_style == 'tab':
            lines.append("indent_size = tab")
        
        # EOL
        eol = determine_setting(props['eol'], default='lf')
        lines.append(f"end_of_line = {eol}")
        
        # Charset
        charset = determine_setting(props['charset'], default='utf-8')
        lines.append(f"charset = {charset}")
        
        lines.append("")  # Add a blank line after each section
    
    return '\n'.join(lines)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Generate an .editorconfig file based on existing files.'
    )
    parser.add_argument(
        'paths',
        nargs='*',
        default=['.'],
        help='Optional paths or glob patterns to scan. Defaults to current directory.'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Overwrite existing .editorconfig if it exists.'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode to output detailed analysis.'
    )
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Check if .editorconfig exists
    editorconfig_path = os.path.join(os.getcwd(), '.editorconfig')
    if os.path.exists(editorconfig_path) and not args.force:
        print("`.editorconfig` already exists. Use --force (-f) to overwrite.", file=sys.stderr)
        sys.exit(1)
    elif os.path.exists(editorconfig_path) and args.force:
        if args.debug:
            print(f"Overwriting existing `.editorconfig` at {editorconfig_path}")

    # Initialize file_properties as a defaultdict of lists
    file_properties = defaultdict(list)
    
    # Initialize libmagic
    try:
        mime = magic.Magic(mime=True)
    except Exception as e:
        print(f"Error initializing libmagic: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Expand glob patterns and collect files
    files_to_scan = set()
    for pattern in args.paths:
        matched = glob.glob(pattern, recursive=True)
        if not matched:
            print(f"No files matched the pattern: {pattern}", file=sys.stderr)
        for path in matched:
            if os.path.isfile(path):
                files_to_scan.add(os.path.abspath(path))
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    # Modify dirs in-place to skip excluded directories
                    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
                    for file in files:
                        filepath = os.path.join(root, file)
                        files_to_scan.add(os.path.abspath(filepath))
    
    # Analyze each file
    for filepath in files_to_scan:
        # Skip binary files using libmagic
        if is_binary_file(filepath, mime=mime):
            if args.debug:
                print(f"Skipping binary file: {filepath}")
            continue
        ext = get_file_extension(filepath)
        props = analyze_file(filepath, mime=mime, debug=args.debug)
        # Only consider files with identifiable indentation and EOL
        if props['indent_style'] and props['eol']:
            file_properties[ext].append(props)  # Append props dict to the list for the extension
        else:
            if args.debug:
                print(f"Skipping file due to incomplete analysis: {filepath}")

    if args.debug:
        print("\n--- Aggregating Properties ---\n")
    
    # Aggregate properties with equal weighting for each file
    aggregated = aggregate_properties(file_properties, debug=args.debug)
    
    if args.debug:
        print("\n--- Aggregated Properties ---\n")
    
    editorconfig_content = generate_editorconfig(aggregated, debug=args.debug)
    
    try:
        with open(editorconfig_path, 'w', encoding='utf-8') as f:
            f.write(editorconfig_content)
        print("`.editorconfig` has been generated based on the analyzed files.")
    except Exception as e:
        print(f"Error writing .editorconfig: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

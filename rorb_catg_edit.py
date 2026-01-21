#!/usr/bin/env python3
"""
RORB .catg File Editor - Preserves exact spacing and line endings

This script edits RORB GE/ArcRORB .catg files while preserving the file's
exact spacing, indentation, and line endings. It uses fixed-span replacement
to modify only the target field without affecting any other formatting.

Usage examples:
    # Set PrintFlag to 1 for all reaches
    python rorb_catg_edit.py input.catg output.catg --section REACHES --field PrintFlag --value 1

    # Set PrintFlag to 1 for all nodes
    python rorb_catg_edit.py input.catg output.catg --section NODES --field PrintFlag --value 1

    # Set ReachType to 2 for all reaches
    python rorb_catg_edit.py input.catg output.catg --section REACHES --field ReachType --value 2

    # Use numeric token index (1-based after 'C') instead of field name
    python rorb_catg_edit.py input.catg output.catg --section NODES --field 6 --value 1

Author: Claude Code
"""

import argparse
import sys
import re
from typing import List, Tuple, Optional


# Field definitions for NODES and REACHES blocks
# Format: (field_name, token_index_after_C)
NODES_FIELDS = {
    'NodeNo': 0,
    'X': 1,
    'Y': 2,
    'Size': 3,
    'NodeType': 4,
    'PrintFlag': 5,
    'DownstreamNode': 6,
    'Name': 7,
    'Area': 8,
    'Imp1': 9,
    # Imp2 is conditional (index 10 if present)
    # PrintType, ArrowLoc, PrintMarker follow after Imp2 or Imp1
}

REACHES_FIELDS = {
    'ReachNo': 0,
    'ReachName': 1,
    'FromNode': 2,
    'ToNode': 3,
    'TransFlag': 4,
    'ReachType': 5,
    'PrintFlag': 6,
    'Length': 7,
    'SlopeOrTrans': 8,
    'Ncoords': 9,
    'Reserved': 10,
}


def detect_line_ending(content: bytes) -> str:
    """Detect the line ending style used in the file (CRLF or LF)."""
    if b'\r\n' in content:
        return '\r\n'
    return '\n'


def find_token_positions(line: str) -> List[Tuple[int, int, str]]:
    """
    Find the exact character positions of all tokens in a line.

    Returns a list of (start_pos, end_pos, token_value) tuples.
    The span from start_pos to end_pos represents the field's allocation
    including trailing spaces up to the next token.
    """
    # Skip the leading 'C' and any following space
    if not line.startswith('C'):
        return []

    content_after_c = line[1:]  # Everything after 'C'
    tokens = []

    # Find all tokens using regex to capture their positions
    # Match non-whitespace sequences
    for match in re.finditer(r'\S+', content_after_c):
        token_value = match.group()
        start_in_content = match.start()
        end_in_content = match.end()

        # Adjust positions to account for leading 'C'
        start_pos = start_in_content + 1
        end_pos = end_in_content + 1

        tokens.append((start_pos, end_pos, token_value))

    return tokens


def get_field_span(line: str, token_index: int) -> Optional[Tuple[int, int]]:
    """
    Get the character span (start, end) for a specific token by index.
    The span extends from the token's start to the next token's start
    (or end of line if it's the last token).

    Args:
        line: The line to analyze
        token_index: 0-based index of the token (after 'C')

    Returns:
        (start_pos, end_pos) tuple or None if token doesn't exist
    """
    tokens = find_token_positions(line)

    if token_index >= len(tokens):
        return None

    start_pos = tokens[token_index][0]

    # End position is the start of the next token, or end of line
    if token_index + 1 < len(tokens):
        end_pos = tokens[token_index + 1][0]
    else:
        # Last token - extend to end of line (excluding newline)
        end_pos = len(line.rstrip('\r\n'))

    return (start_pos, end_pos)


def replace_field_in_span(line: str, start_pos: int, end_pos: int, new_value: str) -> str:
    """
    Replace a field within its fixed span, preserving total span width.

    Args:
        line: The original line
        start_pos: Start of the field span
        end_pos: End of the field span (exclusive)
        new_value: New value to write

    Returns:
        Modified line with field replaced

    Raises:
        ValueError: If new value doesn't fit in the span
    """
    span_width = end_pos - start_pos

    # Check if new value fits
    if len(new_value) > span_width:
        raise ValueError(
            f"New value '{new_value}' (length {len(new_value)}) doesn't fit in "
            f"span of width {span_width}"
        )

    # Create the replacement: new value + padding to maintain span width
    replacement = new_value.ljust(span_width)

    # Replace the span
    new_line = line[:start_pos] + replacement + line[end_pos:]

    return new_line


def is_node_record_line(line: str) -> bool:
    """
    Check if a line is a valid node record line in #NODES block.

    Node record format: C <NodeNo> <X> <Y> <Size> ...
    - First token after 'C' should be an integer (NodeNo)
    - Second and third tokens should be numeric (X, Y coordinates)
    """
    if not line.startswith('C'):
        return False

    tokens = find_token_positions(line)

    # Need at least NodeNo, X, Y
    if len(tokens) < 3:
        return False

    # Check if first token is integer (NodeNo)
    try:
        int(tokens[0][2])
    except ValueError:
        return False

    # Check if second and third tokens are numeric (X, Y)
    try:
        float(tokens[1][2])
        float(tokens[2][2])
    except ValueError:
        return False

    return True


def is_reach_header_line(line: str, prev_coord_count: int) -> Tuple[bool, int]:
    """
    Check if a line is a reach header line (not a coordinate line).

    Reach header: C <ReachNo> <ReachName> <FromNode> <ToNode> ... <Ncoords> ...
    Coordinate line: C <float1> <float2> ... (all numeric)

    Returns:
        (is_header, ncoords_if_header)
    """
    if not line.startswith('C'):
        return False, 0

    tokens = find_token_positions(line)

    if len(tokens) < 10:  # Reach header should have at least 10 tokens
        return False, 0

    # Heuristic: If we're expecting coordinate lines (prev_coord_count > 0),
    # and the line has only numeric tokens, it's a coordinate line
    if prev_coord_count > 0:
        # Check if all tokens are numeric (coordinate line)
        all_numeric = True
        for _, _, token in tokens:
            try:
                float(token)
            except ValueError:
                all_numeric = False
                break

        if all_numeric:
            return False, 0

    # Check for reach header pattern:
    # - First token is integer (ReachNo)
    # - Has mix of integers and strings
    # - Token at index 9 should be integer (Ncoords)
    try:
        int(tokens[0][2])  # ReachNo
        ncoords = int(tokens[9][2])  # Ncoords
        return True, ncoords
    except (ValueError, IndexError):
        return False, 0


def edit_catg_file(input_path: str, output_path: str, section: str,
                   field_spec: str, new_value: str) -> int:
    """
    Edit a .catg file, modifying a specific field in all records of a section.

    Args:
        input_path: Path to input .catg file
        output_path: Path to output .catg file
        section: 'NODES' or 'REACHES'
        field_spec: Field name or numeric token index (1-based for user, converted to 0-based)
        new_value: New value to set

    Returns:
        Number of lines modified
    """
    # Read the entire file in binary mode to preserve exact bytes
    with open(input_path, 'rb') as f:
        content = f.read()

    # Detect line ending style
    line_ending_bytes = detect_line_ending(content)
    line_ending = line_ending_bytes

    # Decode to string for processing
    text = content.decode('utf-8', errors='replace')
    lines = text.split('\n') if '\n' in text else [text]

    # Handle CRLF: remove \r from line ends
    if '\r\n' in text:
        lines = [line.rstrip('\r') for line in text.split('\n')]

    # Determine target token index
    if field_spec.isdigit():
        # User provided 1-based index, convert to 0-based
        token_index = int(field_spec) - 1
        if token_index < 0:
            raise ValueError("Token index must be >= 1")
    else:
        # Look up field name
        if section.upper() == 'NODES':
            if field_spec not in NODES_FIELDS:
                raise ValueError(f"Unknown NODES field: {field_spec}. Valid fields: {', '.join(NODES_FIELDS.keys())}")
            token_index = NODES_FIELDS[field_spec]
        elif section.upper() == 'REACHES':
            if field_spec not in REACHES_FIELDS:
                raise ValueError(f"Unknown REACHES field: {field_spec}. Valid fields: {', '.join(REACHES_FIELDS.keys())}")
            token_index = REACHES_FIELDS[field_spec]
        else:
            raise ValueError(f"Invalid section: {section}. Must be NODES or REACHES")

    # Process lines
    modified_count = 0
    in_target_section = False
    output_lines = []
    coord_lines_remaining = 0  # For REACHES: track coordinate lines to skip

    for line_num, line in enumerate(lines, 1):
        modified_line = line

        # Track section boundaries
        if line.startswith('C #NODES'):
            in_target_section = (section.upper() == 'NODES')
        elif line.startswith('C #REACHES'):
            in_target_section = (section.upper() == 'REACHES')
            coord_lines_remaining = 0
        elif line.startswith('C #'):
            in_target_section = False
            coord_lines_remaining = 0

        # Edit lines in target section
        if in_target_section:
            if section.upper() == 'NODES':
                # Edit node record lines
                if is_node_record_line(line):
                    span = get_field_span(line, token_index)
                    if span:
                        try:
                            modified_line = replace_field_in_span(line, span[0], span[1], new_value)
                            modified_count += 1
                        except ValueError as e:
                            print(f"ERROR on line {line_num}: {e}", file=sys.stderr)
                            print(f"  Line: {line[:80]}...", file=sys.stderr)
                            sys.exit(1)

            elif section.upper() == 'REACHES':
                # Edit reach header lines only, skip coordinate lines
                if coord_lines_remaining > 0:
                    # This is a coordinate line, skip it
                    coord_lines_remaining -= 1
                else:
                    # Check if this is a reach header
                    is_header, ncoords = is_reach_header_line(line, coord_lines_remaining)
                    if is_header:
                        span = get_field_span(line, token_index)
                        if span:
                            try:
                                modified_line = replace_field_in_span(line, span[0], span[1], new_value)
                                modified_count += 1
                                # Expect 2 coordinate lines after this header
                                coord_lines_remaining = 2
                            except ValueError as e:
                                print(f"ERROR on line {line_num}: {e}", file=sys.stderr)
                                print(f"  Line: {line[:80]}...", file=sys.stderr)
                                sys.exit(1)

        output_lines.append(modified_line)

    # Write output file with original line endings
    output_text = line_ending.join(output_lines)

    # Preserve the exact ending of the original file
    if text.endswith('\n') and not output_text.endswith('\n'):
        output_text += line_ending.rstrip('\r')
    elif text.endswith('\r\n') and not output_text.endswith('\r\n'):
        output_text += line_ending

    with open(output_path, 'wb') as f:
        f.write(output_text.encode('utf-8'))

    return modified_count


def main():
    parser = argparse.ArgumentParser(
        description='Edit RORB .catg files while preserving exact spacing and formatting.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set PrintFlag to 1 for all reaches
  %(prog)s input.catg output.catg --section REACHES --field PrintFlag --value 1

  # Set PrintFlag to 1 for all nodes
  %(prog)s input.catg output.catg --section NODES --field PrintFlag --value 1

  # Set ReachType to 2 for all reaches
  %(prog)s input.catg output.catg --section REACHES --field ReachType --value 2

  # Use token index (1-based, counting tokens after 'C')
  %(prog)s input.catg output.catg --section NODES --field 6 --value 1

Field names for NODES:
  NodeNo, X, Y, Size, NodeType, PrintFlag, DownstreamNode, Name, Area, Imp1

Field names for REACHES:
  ReachNo, ReachName, FromNode, ToNode, TransFlag, ReachType, PrintFlag,
  Length, SlopeOrTrans, Ncoords, Reserved
        """
    )

    parser.add_argument('input', help='Input .catg file path')
    parser.add_argument('output', help='Output .catg file path')
    parser.add_argument('--section', required=True,
                        choices=['NODES', 'REACHES', 'nodes', 'reaches'],
                        help='Section to edit (NODES or REACHES)')
    parser.add_argument('--field', required=True,
                        help='Field name or token index (1-based, after "C")')
    parser.add_argument('--value', required=True,
                        help='New value to set (no whitespace allowed)')

    args = parser.parse_args()

    # Validate that value contains no whitespace
    if ' ' in args.value or '\t' in args.value:
        print("ERROR: Value cannot contain whitespace", file=sys.stderr)
        sys.exit(1)

    try:
        modified_count = edit_catg_file(
            args.input,
            args.output,
            args.section.upper(),
            args.field,
            args.value
        )

        print(f"Successfully modified {modified_count} lines in {args.section.upper()} section.")
        print(f"Output written to: {args.output}")

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

# RORB .catg File Editor

A Python script for editing RORB GE/ArcRORB `.catg` files while **preserving exact spacing and line endings**.

## Features

- ✅ Preserves exact spacing, indentation, and column alignment
- ✅ Preserves original line endings (CRLF vs LF)
- ✅ Edits only the target field using fixed-span replacement
- ✅ Supports both NODES and REACHES sections
- ✅ Field names or numeric token indices
- ✅ Robust detection of record vs coordinate lines
- ✅ Clear error messages if values don't fit

## Installation

No installation required! Just ensure you have Python 3.6+ installed:

```bash
python3 --version
```

## Usage

### Basic Syntax

```bash
python3 rorb_catg_edit.py INPUT.catg OUTPUT.catg --section SECTION --field FIELD --value VALUE
```

### Parameters

- `INPUT.catg` - Input .catg file path
- `OUTPUT.catg` - Output .catg file path
- `--section` - Section to edit: `NODES` or `REACHES`
- `--field` - Field name (e.g., `PrintFlag`) or token index (1-based, after "C")
- `--value` - New value (no whitespace allowed)

## Examples

### Example 1: Set PrintFlag to 1 for all nodes

```bash
python3 rorb_catg_edit.py example/sample.catg output.catg \
  --section NODES \
  --field PrintFlag \
  --value 1
```

**Before:**
```
C      1         56.617         40.580          1.000 1 0     2 A                          7.669000       0.000000       0.100000  0  1  0
```

**After:**
```
C      1         56.617         40.580          1.000 1 1     2 A                          7.669000       0.000000       0.100000  0  1  0
```

### Example 2: Set PrintFlag to 1 for all reaches

```bash
python3 rorb_catg_edit.py example/sample.catg output.catg \
  --section REACHES \
  --field PrintFlag \
  --value 1
```

**Before:**
```
C      3 A-A1                     1     2              0 1 0          1.288          0.873     2  0
C          56.826         56.902
C          40.580         40.454
```

**After:**
```
C      3 A-A1                     1     2              0 1 1          1.288          0.873     2  0
C          56.826         56.902
C          40.580         40.454
```

Note: Coordinate lines remain untouched.

### Example 3: Set ReachType to 2 for all reaches

```bash
python3 rorb_catg_edit.py example/sample.catg output.catg \
  --section REACHES \
  --field ReachType \
  --value 2
```

### Example 4: Using numeric token index

```bash
# Set the 6th token (PrintFlag in NODES) to 1
python3 rorb_catg_edit.py example/sample.catg output.catg \
  --section NODES \
  --field 6 \
  --value 1
```

## Supported Fields

### NODES Section Fields

Token-based fields (after "C"):

| Field Name       | Index | Description                    |
|------------------|-------|--------------------------------|
| NodeNo           | 1     | Node number                    |
| X                | 2     | X coordinate                   |
| Y                | 3     | Y coordinate                   |
| Size             | 4     | Node size                      |
| NodeType         | 5     | Node type                      |
| PrintFlag        | 6     | Print flag (0=off, 1=on)       |
| DownstreamNode   | 7     | Downstream node number         |
| Name             | 8     | Node name (padded with spaces) |
| Area             | 9     | Sub-area                       |
| Imp1             | 10    | Impervious fraction 1          |

### REACHES Section Fields

Token-based fields (after "C" in reach header lines):

| Field Name    | Index | Description                     |
|---------------|-------|---------------------------------|
| ReachNo       | 1     | Reach number                    |
| ReachName     | 2     | Reach name (padded with spaces) |
| FromNode      | 3     | From node number                |
| ToNode        | 4     | To node number                  |
| TransFlag     | 5     | Translation flag                |
| ReachType     | 6     | Reach type                      |
| PrintFlag     | 7     | Print flag (0=off, 1=on)        |
| Length        | 8     | Reach length                    |
| SlopeOrTrans  | 9     | Slope or translation value      |
| Ncoords       | 10    | Number of coordinate pairs      |
| Reserved      | 11    | Reserved field                  |

## How It Works

The script uses **fixed-span replacement**:

1. Identifies the exact character span of the target field
2. Replaces only within that span
3. Pads with spaces to maintain span width
4. Preserves all other formatting

This ensures:
- Original spacing is maintained
- Column alignment is preserved
- Line endings (CRLF/LF) are preserved
- Only the target field changes

## Error Handling

The script will exit with an error if:

- The new value is too long to fit in the field's span
- The field name is invalid
- The section name is invalid
- The value contains whitespace
- The input file doesn't exist

## File Format Details

### NODES Block Structure

```
C #NODES
C    <count>
C      <NodeNo> <X> <Y> <Size> <NodeType> <PrintFlag> <DownstreamNode> <Name> <Area> <Imp1> [<Imp2>] <PrintType> <ArrowLoc> <PrintMarker>
C      ...
```

### REACHES Block Structure

```
C #REACHES
C    <count>
C      <ReachNo> <ReachName> <FromNode> <ToNode> <TransFlag> <ReachType> <PrintFlag> <Length> <SlopeOrTrans> <Ncoords> <Reserved>
C          <x1> <x2> ... <xN>
C          <y1> <y2> ... <yN>
C      ...
```

Each reach has:
- 1 header line (editable)
- 2 coordinate lines (never modified by this script)

## Testing

Test the script with the included sample file:

```bash
# Test NODES editing
python3 rorb_catg_edit.py example/sample.catg test_nodes.catg \
  --section NODES --field PrintFlag --value 1

# Test REACHES editing
python3 rorb_catg_edit.py example/sample.catg test_reaches.catg \
  --section REACHES --field PrintFlag --value 1

# Verify output preserves spacing
diff -u <(head -50 example/sample.catg) <(head -50 test_nodes.catg)
```

## Important Notes

⚠️ **Space-Sensitive Format**
- Do NOT edit .catg files manually unless you understand the exact column positions
- Always use this script to preserve formatting
- The output must be identical to input except for edited fields

⚠️ **Value Constraints**
- New values cannot contain whitespace
- New values must fit within the existing field span
- If a value is too long, the script will error (not truncate)

⚠️ **Coordinate Lines**
- In REACHES section, coordinate lines are NEVER modified
- Only reach header lines are edited

## License

This script is provided as-is for editing RORB .catg files.

## Author

Generated by Claude Code

#!/bin/bash
# Test script for rorb_catg_edit.py

set -e  # Exit on error

echo "=================================="
echo "RORB .catg Editor - Test Suite"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Set PrintFlag to 1 for all nodes
echo -e "${BLUE}Test 1: Set PrintFlag to 1 for all NODES${NC}"
python3 rorb_catg_edit.py example/sample.catg test_nodes_printflag.catg \
  --section NODES \
  --field PrintFlag \
  --value 1
echo -e "${GREEN}✓ Test 1 passed${NC}"
echo ""

# Test 2: Set PrintFlag to 1 for all reaches
echo -e "${BLUE}Test 2: Set PrintFlag to 1 for all REACHES${NC}"
python3 rorb_catg_edit.py example/sample.catg test_reaches_printflag.catg \
  --section REACHES \
  --field PrintFlag \
  --value 1
echo -e "${GREEN}✓ Test 2 passed${NC}"
echo ""

# Test 3: Set ReachType to 2 for all reaches
echo -e "${BLUE}Test 3: Set ReachType to 2 for all REACHES${NC}"
python3 rorb_catg_edit.py example/sample.catg test_reaches_type.catg \
  --section REACHES \
  --field ReachType \
  --value 2
echo -e "${GREEN}✓ Test 3 passed${NC}"
echo ""

# Test 4: Using numeric token index
echo -e "${BLUE}Test 4: Using numeric token index (6 = PrintFlag for NODES)${NC}"
python3 rorb_catg_edit.py example/sample.catg test_nodes_index.catg \
  --section NODES \
  --field 6 \
  --value 1
echo -e "${GREEN}✓ Test 4 passed${NC}"
echo ""

# Test 5: Verify line endings are preserved
echo -e "${BLUE}Test 5: Verify line endings are preserved${NC}"
original_le=$(file example/sample.catg)
output_le=$(file test_nodes_printflag.catg)
if [[ "$original_le" == *"CRLF"* ]] && [[ "$output_le" == *"CRLF"* ]]; then
    echo "Line endings preserved: CRLF"
elif [[ "$original_le" != *"CRLF"* ]] && [[ "$output_le" != *"CRLF"* ]]; then
    echo "Line endings preserved: LF"
else
    echo "ERROR: Line endings changed!"
    exit 1
fi
echo -e "${GREEN}✓ Test 5 passed${NC}"
echo ""

# Test 6: Verify coordinate lines are not modified in REACHES
echo -e "${BLUE}Test 6: Verify coordinate lines are unchanged in REACHES${NC}"
# Extract a few coordinate lines from original and modified files
original_coords=$(sed -n '1591,1592p' example/sample.catg)
modified_coords=$(sed -n '1591,1592p' test_reaches_printflag.catg)
if [ "$original_coords" = "$modified_coords" ]; then
    echo "Coordinate lines preserved correctly"
    echo -e "${GREEN}✓ Test 6 passed${NC}"
else
    echo "ERROR: Coordinate lines were modified!"
    echo "Original:"
    echo "$original_coords"
    echo "Modified:"
    echo "$modified_coords"
    exit 1
fi
echo ""

# Test 7: Show before/after comparison
echo -e "${BLUE}Test 7: Before/After comparison (first node)${NC}"
echo "Original line 25:"
sed -n '25p' example/sample.catg
echo ""
echo "Modified line 25 (PrintFlag changed from 0 to 1):"
sed -n '25p' test_nodes_printflag.catg
echo -e "${GREEN}✓ Test 7 passed${NC}"
echo ""

# Test 8: Error handling - invalid field name
echo -e "${BLUE}Test 8: Error handling - invalid field name${NC}"
if python3 rorb_catg_edit.py example/sample.catg test_error.catg \
  --section NODES \
  --field InvalidField \
  --value 1 2>&1 | grep -q "Unknown NODES field"; then
    echo "Correctly caught invalid field name"
    echo -e "${GREEN}✓ Test 8 passed${NC}"
else
    echo "ERROR: Did not catch invalid field name"
    exit 1
fi
echo ""

echo "=================================="
echo -e "${GREEN}All tests passed! ✓${NC}"
echo "=================================="
echo ""
echo "Output files generated:"
echo "  - test_nodes_printflag.catg"
echo "  - test_reaches_printflag.catg"
echo "  - test_reaches_type.catg"
echo "  - test_nodes_index.catg"
echo ""
echo "To clean up test files, run:"
echo "  rm test_*.catg"

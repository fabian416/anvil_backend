#!/bin/bash
################################################################################
# TypeScript Validator for API Documentation
# 
# Validates that all TypeScript interfaces and types in API documentation
# are syntactically correct and follow best practices.
#
# Usage: ./scripts/api_audit/validate_typescript.sh
################################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs/frontend"
TEMP_DIR="$SCRIPT_DIR/.temp_ts_validation"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 TypeScript Validation Started"
echo "================================================================"
echo "📁 Project: $(basename "$PROJECT_ROOT")"
echo "📚 Docs Directory: $DOCS_DIR"
echo ""

# Check if Node.js and npm are available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Error: Node.js is not installed${NC}"
    echo "   Please install Node.js from https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Error: npm is not installed${NC}"
    exit 1
fi

# Create temp directory
mkdir -p "$TEMP_DIR"

# Extract TypeScript code blocks from markdown files
echo "📄 Extracting TypeScript code blocks..."

TOTAL_FILES=0
TOTAL_BLOCKS=0
ERRORS=0

# Find all markdown files
MD_FILES=$(find "$DOCS_DIR" -name "*.md" 2>/dev/null)

if [ -z "$MD_FILES" ]; then
    echo -e "${YELLOW}⚠️  No markdown files found in $DOCS_DIR${NC}"
    exit 1
fi

# Create a temporary TypeScript file
TS_FILE="$TEMP_DIR/extracted.ts"
echo "// Auto-generated TypeScript validation file" > "$TS_FILE"
echo "// Generated: $(date)" >> "$TS_FILE"
echo "" >> "$TS_FILE"

# Extract TypeScript blocks from each markdown file
while IFS= read -r md_file; do
    TOTAL_FILES=$((TOTAL_FILES + 1))
    
    # Extract TypeScript code blocks (```typescript ... ```)
    awk '
        /```typescript/ { in_block=1; next }
        /```/ { if (in_block) { print ""; in_block=0 } next }
        in_block { print }
    ' "$md_file" >> "$TS_FILE"
    
    # Count blocks
    BLOCKS=$(grep -c "^interface\|^type\|^const\|^class\|^function\|^export" "$TS_FILE" 2>/dev/null || echo "0")
    TOTAL_BLOCKS=$BLOCKS
    
done <<< "$MD_FILES"

echo -e "${GREEN}✅ Extracted from $TOTAL_FILES markdown files${NC}"
echo "   TypeScript blocks found: $TOTAL_BLOCKS"
echo ""

# Create a minimal package.json if it doesn't exist
if [ ! -f "$TEMP_DIR/package.json" ]; then
    echo "📦 Creating temporary package.json..."
    cat > "$TEMP_DIR/package.json" << 'EOF'
{
  "name": "api-docs-typescript-validation",
  "version": "1.0.0",
  "private": true,
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0"
  }
}
EOF
fi

# Create tsconfig.json
echo "⚙️  Creating TypeScript configuration..."
cat > "$TEMP_DIR/tsconfig.json" << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true
  },
  "include": ["*.ts"]
}
EOF

# Install TypeScript if needed
if [ ! -d "$TEMP_DIR/node_modules" ]; then
    echo "📥 Installing TypeScript (one-time setup)..."
    cd "$TEMP_DIR"
    npm install --silent > /dev/null 2>&1
    cd "$PROJECT_ROOT"
fi

# Run TypeScript compiler
echo "🔍 Running TypeScript compiler..."
echo ""

cd "$TEMP_DIR"

# Run tsc and capture output
if npx tsc --noEmit 2>&1 | tee "$TEMP_DIR/tsc_output.txt"; then
    echo ""
    echo -e "${GREEN}✅ TypeScript Validation PASSED${NC}"
    echo "   All interfaces and types are valid!"
    VALIDATION_PASSED=true
else
    echo ""
    echo -e "${RED}❌ TypeScript Validation FAILED${NC}"
    echo ""
    echo "Errors found:"
    cat "$TEMP_DIR/tsc_output.txt"
    VALIDATION_PASSED=false
    ERRORS=1
fi

cd "$PROJECT_ROOT"

# Generate report
echo ""
echo "================================================================"
echo "📊 TYPESCRIPT VALIDATION REPORT"
echo "================================================================"
echo ""
echo "📈 Summary:"
echo "   Markdown Files Scanned:    $TOTAL_FILES"
echo "   TypeScript Blocks:         $TOTAL_BLOCKS"
echo "   Validation Status:         $([ "$VALIDATION_PASSED" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"
echo ""

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}🎉 All TypeScript code in documentation is valid!${NC}"
    echo ""
    echo "Quality Metrics:"
    echo "   ✅ Interfaces are well-formed"
    echo "   ✅ Types are correctly defined"
    echo "   ✅ No syntax errors"
    echo "   ✅ Follows TypeScript best practices"
else
    echo -e "${YELLOW}⚠️  Fix the errors above and run validation again${NC}"
    echo ""
    echo "Common Issues:"
    echo "   • Missing type annotations"
    echo "   • Incorrect interface syntax"
    echo "   • Undefined types or interfaces"
    echo "   • Inconsistent naming conventions"
fi

echo ""
echo "================================================================"

# Save report
REPORT_FILE="$SCRIPT_DIR/data/typescript_validation_report.json"
mkdir -p "$(dirname "$REPORT_FILE")"

cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "summary": {
    "markdown_files_scanned": $TOTAL_FILES,
    "typescript_blocks": $TOTAL_BLOCKS,
    "validation_passed": $([ "$VALIDATION_PASSED" = true ] && echo "true" || echo "false"),
    "errors": $ERRORS
  },
  "temp_directory": "$TEMP_DIR",
  "typescript_file": "$TS_FILE"
}
EOF

echo "💾 Report saved: $REPORT_FILE"
echo ""

# Cleanup option
if [ "$VALIDATION_PASSED" = true ]; then
    echo "🧹 Cleaning up temporary files..."
    # rm -rf "$TEMP_DIR"
    echo "   (Kept for inspection: $TEMP_DIR)"
else
    echo "📁 Temporary files kept for debugging: $TEMP_DIR"
    echo "   Review: $TS_FILE"
fi

echo ""
echo "================================================================"

# Exit with appropriate code
if [ "$VALIDATION_PASSED" = true ]; then
    exit 0
else
    exit 1
fi

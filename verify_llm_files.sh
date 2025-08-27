#!/bin/bash
# Verify LLM integration files are present and check their git status

echo "🔍 LLM Integration Verification"
echo "==============================="

cd /Volumes/FS001/pythonscripts/Avatar-Engine

echo "📁 Checking for LLM Enhancement Files:"
echo ""

files=(
    "src/config_manager.py"
    "src/llm_integrator.py" 
    "src/enhanced_avatar_pipeline.py"
    "sql/enhanced_avatar_schema.cypher"
    "enhanced_deployment.py"
    "examples/enhanced_demo.py"
    "examples/test_enhanced_system.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        size=$(ls -lh "$file" | awk '{print $5}')
        echo "✅ $file ($size)"
    else
        echo "❌ $file (missing)"
    fi
done

echo ""
echo "📊 Git Status Check:"
git status --porcelain

echo ""
echo "🔍 Checking if files are tracked by git:"
for file in "${files[@]}"; do
    if git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
        echo "📝 $file (tracked)"
    else
        echo "❓ $file (untracked)"
    fi
done

echo ""
echo "💡 If files show as untracked, run:"
echo "   git add ."
echo "   git commit -m 'Add LLM enhancements'"
echo "   git push origin main"

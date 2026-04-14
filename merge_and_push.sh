#!/bin/bash
# Merge remote changes and push

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        Merging Remote and Local Changes                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd ~/AWS_Architecture_explorer/AWS_DOOM/game

echo "📥 Pulling remote changes..."
git pull origin main --allow-unrelated-histories -m "Merge remote with updated game files"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Merge successful!"
    echo ""
    echo "📤 Pushing to GitHub..."
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "╔══════════════════════════════════════════════════════════════╗"
        echo "║                                                              ║"
        echo "║          ✅ Successfully pushed to GitHub! ✅                ║"
        echo "║                                                              ║"
        echo "║  Repository: https://github.com/askjake/AWS_DOOM            ║"
        echo "║                                                              ║"
        echo "╚══════════════════════════════════════════════════════════════╝"
    else
        echo "❌ Push failed"
    fi
else
    echo ""
    echo "⚠️ Merge had conflicts. Resolve them and then:"
    echo "   git add ."
    echo "   git commit -m 'Resolved merge conflicts'"
    echo "   git push -u origin main"
fi

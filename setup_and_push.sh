#!/bin/bash
# AWS DOOM - GitHub SSH Setup and Push Script

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        AWS DOOM - GitHub Setup & Push                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
cd ~/AWS_Architecture_explorer/AWS_DOOM/game

echo "📋 Your SSH Public Key:"
echo ""
cat ~/.ssh/github_aws_doom.pub
echo ""
echo "🔗 Add this key to GitHub: https://github.com/settings/ssh/new"
echo ""
echo "Press Enter after you've added the key to GitHub..."
read

echo ""
echo "🧪 Testing GitHub connection..."
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated" && echo "✅ Connection successful!" || echo "❌ Connection failed - make sure you added the key to GitHub"

echo ""
echo "🔧 Updating git remote to use SSH..."
git remote set-url origin git@github.com:askjake/AWS_DOOM.git
echo "✅ Remote updated"

echo ""
echo "📊 Repository status:"
git remote -v
echo ""

echo "🚀 Ready to push!"
echo ""
echo "Push to GitHub now? (y/n)"
read -r answer

if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
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
        echo ""
        echo "❌ Push failed. Check the error message above."
        echo ""
        echo "Common issues:"
        echo "  - SSH key not added to GitHub"
        echo "  - Repository doesn't exist on GitHub"
        echo "  - Network connectivity issues"
        echo ""
        echo "Try testing connection: ssh -T git@github.com"
    fi
else
    echo ""
    echo "Push cancelled. To push later, run:"
    echo "  cd ~/AWS_Architecture_explorer/AWS_DOOM/game"
    echo "  git push -u origin main"
fi

#!/bin/bash

# 🔐 Quick GitHub Token Authentication
# Fast setup for GitHub CLI using personal access token

echo "🔐 GITHUB CLI TOKEN AUTHENTICATION"
echo "=================================="
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📋 STEP 1: CREATE PERSONAL ACCESS TOKEN${NC}"
echo "----------------------------------------"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token' → 'Generate new token (classic)'"
echo "3. Token settings:"
echo "   - Note: 'COOGI Platform CLI Access'"
echo "   - Expiration: Choose as needed"
echo "   - Required scopes:"
echo "     ✅ repo"
echo "     ✅ workflow" 
echo "     ✅ write:packages"
echo "     ✅ delete_repo"
echo "4. Click 'Generate token' and copy it"
echo
echo -e "${YELLOW}After creating the token, press ENTER to continue...${NC}"
read -p ""

echo -e "\n${BLUE}📋 STEP 2: AUTHENTICATE${NC}"
echo "----------------------------------------"

# Clear existing authentication
echo "Clearing existing GitHub authentication..."
gh auth logout --hostname github.com 2>/dev/null || true

echo "Please paste your GitHub personal access token:"
echo "(Starts with 'ghp_' or 'github_pat_')"
read -s -p "Token: " GITHUB_TOKEN
echo

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ No token provided. Exiting.${NC}"
    exit 1
fi

echo "Authenticating with GitHub..."
echo "$GITHUB_TOKEN" | gh auth login --hostname github.com --with-token

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Authentication successful!${NC}"
    
    # Verify authentication
    echo -e "\n${BLUE}Verifying authentication...${NC}"
    gh auth status
    
    # Get user info
    USERNAME=$(gh api user --jq .login 2>/dev/null)
    if [ -n "$USERNAME" ]; then
        echo -e "\n${GREEN}✅ Logged in as: $USERNAME${NC}"
        echo "You can now run the main setup script: ./github_setup_complete.sh"
    else
        echo -e "\n${YELLOW}⚠️  Authentication successful but couldn't get user info${NC}"
    fi
else
    echo -e "${RED}❌ Authentication failed. Please check your token.${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 Ready to upload your code!${NC}"

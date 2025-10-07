#!/bin/bash

# Quick Setup Script for AWS Quiz Website on EC2
# Run this after connecting to your EC2 instance via PuTTY

echo "🚀 AWS Quiz Website - Quick EC2 Setup"
echo "======================================"

# Check if running on correct user
if [[ "$USER" == "root" ]]; then
    echo "❌ Don't run as root. Switch to ec2-user or ubuntu:"
    echo "   sudo su - ec2-user    # Amazon Linux"
    echo "   sudo su - ubuntu      # Ubuntu"
    exit 1
fi

# Update system and install git
echo "📦 Installing prerequisites..."
if command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y git
else
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y git
fi

# Clone repository
echo "📥 Cloning repository..."
if [ ! -d "aws-quiz-website" ]; then
    git clone https://github.com/Venkat-idexcel/aws-quiz-website.git
    cd aws-quiz-website
else
    echo "✅ Repository already exists, pulling latest changes..."
    cd aws-quiz-website
    git pull origin main
fi

# Make deployment script executable
chmod +x deploy_ec2.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Review the deployment guide: cat EC2_DEPLOYMENT_GUIDE.md"
echo "2. Run the automated deployment: ./deploy_ec2.sh"
echo "3. Or follow manual steps in EC2_DEPLOYMENT_GUIDE.md"
echo ""
echo "📚 Available guides:"
echo "   - EC2_DEPLOYMENT_GUIDE.md    - Complete step-by-step guide"
echo "   - DATABASE_SETUP_GUIDE.md    - Database troubleshooting"
echo ""
echo "🎯 For quick deployment, run:"
echo "   ./deploy_ec2.sh"
echo ""
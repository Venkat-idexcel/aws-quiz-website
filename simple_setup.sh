#!/bin/bash
# Simple EC2 setup for AWS Quiz Website
echo "🚀 AWS Quiz Website - EC2 Setup"
sudo yum update -y && sudo yum install -y git
git clone https://github.com/Venkat-idexcel/aws-quiz-website.git
cd aws-quiz-website
chmod +x deploy_ec2.sh
echo "✅ Setup complete! Run: ./deploy_ec2.sh"
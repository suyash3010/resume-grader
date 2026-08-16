#!/bin/bash

# Resume Grader - AWS SAM Deployment Script
# Deploys Flask application to AWS Lambda + API Gateway (HttpApi)

set -e

echo "╔════════════════════════════════════════════╗"
echo "║  Resume Grader - SAM Deployment Tool      ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install from:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Install from:"
    echo "   https://aws.amazon.com/serverless/sam/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install Python 3.11 or later."
    exit 1
fi

echo "✅ Prerequisites found (AWS CLI, SAM CLI, Python 3)"
echo ""

# Get OpenAI API key
echo "📋 Configuration"
echo "═══════════════════════════════════════════════════════"
read -sp "Enter your OpenAI API key (hidden): " openai_key
echo ""

if [ -z "$openai_key" ]; then
    echo "❌ OpenAI API key is required."
    exit 1
fi

# Get AWS region
echo ""
read -p "Enter AWS region (default: eu-west-1): " aws_region
aws_region=${aws_region:-eu-west-1}

# Get stack name
echo ""
read -p "Enter CloudFormation stack name (default: resume-grader-httpapi): " stack_name
stack_name=${stack_name:-resume-grader-httpapi}

echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "🔨 Building SAM application..."
sam build

echo ""
echo "🚀 Deploying to AWS Lambda..."
echo "   Region: $aws_region"
echo "   Stack: $stack_name"
echo "   This may take 2-3 minutes..."
echo ""

sam deploy \
    --stack-name "$stack_name" \
    --region "$aws_region" \
    --parameter-overrides OpenAIApiKey="$openai_key" \
    --capabilities CAPABILITY_IAM

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Deployment successful!"
echo "════════════════════════════════════════════════════════"
echo ""

# Get and display the API endpoint
echo "📍 Getting your API endpoint..."
endpoint=$(aws cloudformation describe-stacks \
    --stack-name "$stack_name" \
    --region "$aws_region" \
    --query 'Stacks[0].Outputs[?OutputKey==`ResumeGraderApiEndpoint`].OutputValue' \
    --output text)

if [ -n "$endpoint" ]; then
    echo ""
    echo "✨ Your Resume Grader is live at:"
    echo "   $endpoint"
    echo ""
else
    echo "⚠️  Could not retrieve endpoint. Check outputs:"
    echo "   aws cloudformation describe-stacks --stack-name $stack_name --region $aws_region --query 'Stacks[0].Outputs'"
    echo ""
fi

echo "📖 Helpful commands:"
echo "   View logs:"
echo "     aws logs tail /aws/lambda/resume-grader-function --follow"
echo ""
echo "   Update after code changes:"
echo "     ./deploy.sh"
echo ""
echo "   Delete stack and cleanup:"
echo "     aws cloudformation delete-stack --stack-name $stack_name --region $aws_region"
echo ""
echo "🎉 Done!"

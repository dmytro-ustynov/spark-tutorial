#!/bin/bash

# Quick Docker build test script
echo "🔧 Testing Docker build process..."

cd "$(dirname "$0")"

# Test Docker build
echo "Building Docker image..."
if docker build -t spark-tutorial-test . > /dev/null 2>&1; then
    echo "✅ Docker build successful"
    
    # Clean up test image
    docker rmi spark-tutorial-test > /dev/null 2>&1
    echo "🧹 Cleaned up test image"
    
    echo "🎉 Docker build test passed!"
    exit 0
else
    echo "❌ Docker build failed"
    echo "Run 'docker build .' to see detailed error output"
    exit 1
fi

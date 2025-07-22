#!/bin/bash
# Release script for Live HLS Stream Monitor

set -e

echo "🚀 Live HLS Stream Monitor Release Script"
echo "========================================"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Uncommitted changes found. Please commit or stash them first."
    git status --short
    exit 1
fi

# Get version from user or default
read -p "Enter version (e.g., v1.0.0): " version
if [ -z "$version" ]; then
    version="v1.0.0"
fi

# Validate version format
if [[ ! $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Version must be in format vX.Y.Z (e.g., v1.0.0)"
    exit 1
fi

echo ""
echo "📦 Preparing release $version"
echo "=============================="

# Run tests if available
if [ -f "setup.py" ]; then
    echo "🧪 Running setup tests..."
    python setup.py
fi

# Check that the application can start
echo "🔍 Testing application startup..."
timeout 10s python app.py > /dev/null 2>&1 || {
    if [ $? -eq 124 ]; then
        echo "✅ Application starts successfully (timeout reached as expected)"
    else
        echo "❌ Application failed to start"
        exit 1
    fi
}

# Build Docker image if Dockerfile exists
if [ -f "Dockerfile" ]; then
    echo "🐳 Building Docker image..."
    docker build -t live-hls-monitor:$version .
    docker build -t live-hls-monitor:latest .
    echo "✅ Docker images built successfully"
fi

# Create git tag
echo "🏷️  Creating git tag..."
git tag -a "$version" -m "Release $version"

echo ""
echo "🎉 Release $version prepared successfully!"
echo "======================================="
echo ""
echo "Next steps:"
echo "1. Push the tag to GitHub:"
echo "   git push origin $version"
echo ""
echo "2. Push your changes:"
echo "   git push origin main"
echo ""
echo "3. Create a GitHub release:"
echo "   - Go to https://github.com/msahmarani/live-hls-stream-monitor/releases"
echo "   - Click 'Draft a new release'"
echo "   - Select tag: $version"
echo "   - Add release notes"
echo ""
echo "4. Optional: Push Docker images to registry:"
echo "   docker push your-registry/live-hls-monitor:$version"
echo "   docker push your-registry/live-hls-monitor:latest"

echo ""
echo "📋 Release checklist:"
echo "- [ ] Tag created and pushed"
echo "- [ ] GitHub release created with notes"
echo "- [ ] Documentation updated"
echo "- [ ] Docker images pushed (if applicable)"
echo "- [ ] Announcement posted (if applicable)"

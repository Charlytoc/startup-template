#!/bin/bash

# Mobile App Task Runner
# Usage: ./taskfile.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
}

# Check if npm is installed
check_npm() {
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
}

# Install dependencies
install() {
    print_status "Installing dependencies..."
    npm install
    print_success "Dependencies installed successfully!"
}

# Start development server
dev() {
    print_status "Starting Expo development server..."
    print_warning "Make sure your Django server is running on http://localhost:8000"
    
    # Check if dependencies are installed
    if [ ! -d "node_modules" ]; then
        print_warning "Dependencies not found. Installing..."
        install
    fi
    
    npx expo start
}

# Generate API types from Django backend
gen_types() {
    print_status "Generating API types from Django backend..."
    print_warning "Make sure your Django server is running on http://localhost:8000"
        
    # Check if the script exists
    if [ ! -f "scripts/generate-schema.mjs" ]; then
        print_error "Type generation script not found at scripts/generate-schema.mjs"
        exit 1
    fi
    
    # Generate types
    npm run generate-api-types
    
    if [ $? -eq 0 ]; then
        print_success "API types generated successfully!"
        print_status "Types are available at: types/api/schema.d.ts and types/api/types.ts"
    else
        print_error "Failed to generate API types"
        exit 1
    fi
}

# Show help
help() {
    echo "Mobile App Task Runner"
    echo ""
    echo "Usage: ./taskfile.sh [command]"
    echo ""
    echo "Commands:"
    echo "  dev        Start Expo development server"
    echo "  gen-types  Generate TypeScript types from Django API"
    echo "  install    Install npm dependencies"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./taskfile.sh dev"
    echo "  ./taskfile.sh gen-types"
    echo ""
}

# Main command handler
case "${1:-help}" in
    "dev")
        check_node
        check_npm
        dev
        ;;
    "gen-types")
        check_node
        check_npm
        gen_types
        ;;
    "install")
        check_node
        check_npm
        install
        ;;
    "help"|"--help"|"-h")
        help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        help
        exit 1
        ;;
esac

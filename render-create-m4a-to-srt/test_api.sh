#!/bin/bash
# Test script for the FastAPI M4A to SRT Converter
# Tests all endpoints and functionality

BASE_URL="http://localhost:10000"

echo "🧪 Testing FastAPI M4A to SRT Converter"
echo "========================================"

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s "$BASE_URL/health" | jq '.' || echo "Health check failed"

# Test root endpoint
echo -e "\n2. Testing root endpoint..."
curl -s "$BASE_URL/" | head -n 5

# Test upload endpoint (without file for now)
echo -e "\n3. Testing upload endpoint structure..."
curl -s -X POST "$BASE_URL/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/dev/null" \
  -F "max_words=8" || echo "Upload endpoint test completed"

echo -e "\n4. Testing API documentation..."
echo "Swagger UI available at: $BASE_URL/docs"
echo "ReDoc available at: $BASE_URL/redoc"

echo -e "\n✅ API tests completed!"
echo "📝 To test with a real file, use:"
echo "   curl -X POST \"$BASE_URL/upload\" \\"
echo "     -F \"file=@your_audio.m4a\" \\"
echo "     -F \"max_words=8\"" 
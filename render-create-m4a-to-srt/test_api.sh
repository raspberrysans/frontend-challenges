#!/bin/bash

# Test script for M4A to SRT Converter API
# Make sure the server is running on http://127.0.0.1:10000

BASE_URL="http://127.0.0.1:10000"
TEST_FILE="create-subtitles/audios/test.m4a"

echo "🧪 Testing M4A to SRT Converter API"
echo "=================================="

# Test 1: Health Check
echo "1. Testing health endpoint..."
curl -s -X GET "$BASE_URL/health" | jq '.' 2>/dev/null || curl -s -X GET "$BASE_URL/health"
echo -e "\n"

# Test 2: Check if test file exists
echo "2. Checking test file..."
if [ -f "$TEST_FILE" ]; then
    echo "✅ Test file found: $TEST_FILE"
    echo "   File size: $(du -h "$TEST_FILE" | cut -f1)"
else
    echo "❌ Test file not found: $TEST_FILE"
    echo "   Please ensure the file exists and update the path if needed."
    exit 1
fi
echo -e "\n"

# Test 3: Upload and convert
echo "3. Uploading and converting M4A file..."
RESPONSE=$(curl -s -X POST "$BASE_URL/upload" \
  -F "file=@$TEST_FILE" \
  -F "max_words=8" \
  -H "Content-Type: multipart/form-data")

echo "Response:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"

# Extract job_id from response
JOB_ID=$(echo "$RESPONSE" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to get job_id from response"
    exit 1
fi

echo -e "\nJob ID: $JOB_ID"
echo -e "\n"

# Test 4: Check status (poll until complete)
echo "4. Checking processing status..."
MAX_ATTEMPTS=30
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "   Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/status/$JOB_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    echo "   Status: $STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Processing completed!"
        echo "   Full response:"
        echo "$STATUS_RESPONSE" | jq '.' 2>/dev/null || echo "$STATUS_RESPONSE"
        break
    elif [ "$STATUS" = "error" ]; then
        echo "❌ Processing failed!"
        echo "   Error response:"
        echo "$STATUS_RESPONSE" | jq '.' 2>/dev/null || echo "$STATUS_RESPONSE"
        exit 1
    fi
    
    # Wait 5 seconds before next check
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "❌ Timeout waiting for processing to complete"
    exit 1
fi

echo -e "\n"

# Test 5: Download the SRT file
echo "5. Downloading SRT file..."
curl -s -X GET "$BASE_URL/download/$JOB_ID" \
  -H "Accept: text/plain" \
  -o "test_output.srt"

if [ -f "test_output.srt" ]; then
    echo "✅ SRT file downloaded: test_output.srt"
    echo "   File size: $(du -h test_output.srt | cut -f1)"
    echo "   First few lines:"
    head -10 test_output.srt
else
    echo "❌ Failed to download SRT file"
    exit 1
fi

echo -e "\n"
echo "🎉 All tests completed successfully!"
echo "   SRT file saved as: test_output.srt" 
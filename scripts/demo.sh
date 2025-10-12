#!/bin/bash

# Kairo Health Check Demo Script
# Tests the socket server health check functionality

echo "🔍 Testing Kairo health check..."
echo

# Test ping command
echo "Testing ping command:"
echo -n "ping" | nc -w1 127.0.0.1 9000
echo

# Test other command
echo "Testing other command:"
echo -n "hello" | nc -w1 127.0.0.1 9000
echo

echo
echo "✅ Health check test completed!"
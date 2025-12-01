#!/bin/bash
# Performance monitoring script for AWS Quiz Website
# Run this script to monitor application performance under load

echo "🔍 AWS Quiz Website - Performance Monitor"
echo "========================================="

# Function to display header
display_header() {
    echo ""
    echo "📊 $1"
    echo "----------------------------------------"
}

# Check if services are running
display_header "Service Status"
sudo systemctl is-active aws-quiz-app && echo "✅ Quiz App: Running" || echo "❌ Quiz App: Stopped"
sudo systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Stopped"

# Show current connections
display_header "Current Connections"
echo "Active connections to port 5000 (Gunicorn):"
sudo netstat -an | grep :5000 | wc -l

echo "Active connections to port 80 (Nginx):"
sudo netstat -an | grep :80 | wc -l

echo "Total TCP connections:"
sudo netstat -an | grep ESTABLISHED | wc -l

# Show process information
display_header "Process Information"
echo "Gunicorn processes:"
ps aux | grep gunicorn | grep -v grep | wc -l

echo "Gunicorn worker memory usage:"
ps aux | grep gunicorn | grep -v grep | awk '{sum+=$6} END {print sum/1024 " MB"}'

# Show system resources
display_header "System Resources"
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1

echo "Memory Usage:"
free -h | grep Mem | awk '{print "Used: " $3 " / " $2 " (" $3/$2*100 "%)"}'

echo "Load Average:"
uptime | awk -F'load average:' '{print $2}'

# Show nginx status
display_header "Nginx Status"
if command -v curl >/dev/null 2>&1; then
    echo "Health check:"
    curl -s http://localhost/health || echo "Health check failed"
    
    echo "Response time test:"
    curl -o /dev/null -s -w "Response time: %{time_total}s\n" http://localhost/
else
    echo "curl not available for testing"
fi

# Show recent errors
display_header "Recent Errors (Last 50 lines)"
echo "Application errors:"
sudo journalctl -u aws-quiz-app --no-pager -n 10 | grep -i error || echo "No recent errors"

echo "Nginx errors:"
sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No nginx error log"

# Show access patterns
display_header "Access Patterns (Last 100 requests)"
if [ -f /var/log/nginx/access.log ]; then
    echo "Top 10 IP addresses:"
    sudo tail -n 100 /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
    
    echo "Response codes:"
    sudo tail -n 100 /var/log/nginx/access.log | awk '{print $9}' | sort | uniq -c
    
    echo "Average response time (last 10 requests):"
    sudo tail -n 10 /var/log/nginx/access.log | grep -o 'rt=[0-9]*\.[0-9]*' | cut -d'=' -f2 | awk '{sum+=$1; count++} END {if(count>0) print sum/count "s"; else print "No data"}'
else
    echo "No access log found"
fi

# Performance recommendations
display_header "Performance Recommendations"
current_connections=$(sudo netstat -an | grep :80 | wc -l)
gunicorn_procs=$(ps aux | grep gunicorn | grep -v grep | wc -l)

if [ $current_connections -gt 1000 ]; then
    echo "⚠️  High connection count ($current_connections). Consider scaling horizontally."
fi

if [ $gunicorn_procs -lt 8 ]; then
    echo "⚠️  Low Gunicorn worker count ($gunicorn_procs). Consider increasing workers."
fi

echo ""
echo "🔄 To run continuous monitoring:"
echo "   watch -n 5 $0"
echo ""
echo "📈 To stress test:"
echo "   ab -n 1000 -c 100 http://localhost/"
echo "   wrk -t12 -c400 -d30s http://localhost/"
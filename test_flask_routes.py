"""
Minimal Flask test to verify the application structure is working
"""
from flask import Flask, request, render_template_string
import sys
sys.path.insert(0, 'c:\\Users\\venkatasai.p\\Documents\\aws_quiz_website')

print("\n" + "="*80)
print("🧪 MINIMAL FLASK TEST")
print("="*80)

# Import the app
try:
    from app import app
    print("✅ Successfully imported app")
    
    # Check if app is a Flask instance
    print(f"✅ App type: {type(app)}")
    print(f"✅ App name: {app.name}")
    
    # List all registered routes
    print("\n📍 Registered Routes:")
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"   {rule.rule:40} -> {rule.endpoint:30} [{methods}]")
    
    # Check if login route is registered
    login_routes = [rule for rule in app.url_map.iter_rules() if 'login' in rule.rule]
    print(f"\n🔐 Login routes found: {len(login_routes)}")
    for route in login_routes:
        print(f"   - {route.rule} -> {route.endpoint}")
    
    print("\n✅ Flask app is properly configured!")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

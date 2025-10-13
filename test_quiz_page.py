import requests
import json

# Test if the Flask app can properly handle AWS Data Engineer quiz requests

def test_data_engineer_quiz():
    try:
        base_url = "http://127.0.0.1:5000"
        
        # Test if quiz page loads
        response = requests.get(f"{base_url}/quiz")
        print(f"Quiz page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Quiz page loads successfully")
            
            # Check if we can find AWS Data Engineer option in the page
            if "aws-data-engineer" in response.text:
                print("✅ AWS Data Engineer option found in quiz page")
            else:
                print("❌ AWS Data Engineer option NOT found in quiz page")
                
        else:
            print(f"❌ Quiz page failed to load: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"❌ Error testing: {e}")

if __name__ == "__main__":
    test_data_engineer_quiz()
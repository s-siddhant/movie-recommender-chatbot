import requests
import json

def test_movie_recommendation():
    url = "http://localhost:5000/recommend"
    
    test_cases = [
        {"movie": "Inception"},
        {"movie": ""},
        {"movie": "The Matrix"}
    ]
    
    for test_case in test_cases:
        print("\n" + "="*50)
        print(f"Testing with movie: {test_case['movie']}")
        
        try:
            response = requests.post(url, json=test_case)
            print(f"Status Code: {response.status_code}")
            
            # Print raw response for debugging
            print("Raw Response:")
            print(response.text)
            
            # Print parsed JSON
            print("\nParsed Response:")
            print(json.dumps(response.json(), indent=2))
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {str(e)}")

if __name__ == "__main__":
    test_movie_recommendation()
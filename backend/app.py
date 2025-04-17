from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.chatbot_engine import chat_about_movie

app = Flask(__name__)
CORS(app)

@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json()
        user_input = data.get("movie")

        if not user_input:
            return jsonify({"error": "No movie input provided"}), 400
        
        # Get response from chatbot
        response = chat_about_movie(user_input)
        
        # Check if response is a dictionary
        if isinstance(response, dict):
            return jsonify({"response": response})
        # If response is a string
        else:
            return jsonify({"response": {"text": response}})
            
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug logging
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
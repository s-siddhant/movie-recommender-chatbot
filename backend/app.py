from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.chatbot_engine import chat_about_movie
import logging

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json()
        user_input = data.get("movie")

        if not user_input:
            return jsonify({"error": "No movie input provided"}), 400
        
        # Get response from chatbot
        logger.info(f"Processing request for movie: {user_input}")
        response = chat_about_movie(user_input)
        
        # Return the response with proper structure
        if isinstance(response, dict) and "text" in response:
            return jsonify({
                "response": {
                    "text": response["text"],
                    "context": response.get("context", {})
                },
                "error": None
            })
        else:
            return jsonify({
                "response": {"text": str(response)},
                "error": None
            })
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
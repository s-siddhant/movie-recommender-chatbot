from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.chatbot_engine import chat_about_movie
import logging

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/initialize", methods=["POST"])
def initialize_chat():
    try:
        data = request.get_json()
        movie_name = data.get("movie")

        if not movie_name:
            return jsonify({"error": "No movie input provided"}), 400
        
        # Get initial analysis and context
        logger.info(f"Initializing chat for movie: {movie_name}")
        response = chat_about_movie(movie_name)
        
        if isinstance(response, dict):
            return jsonify({
                "success": True,
                "initial_response": "Here are some recommendations based on your selection:",
                "recommendations": response.get("text", ""),
                "context": response.get("context", {})
            })
        else:
            return jsonify({"error": "Failed to analyze movie"}), 500

    except Exception as e:
        logger.error(f"Error initializing chat: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message")
        context = data.get("context")

        if not user_input or not context:
            return jsonify({"error": "Missing message or context"}), 400

        # Get response using context
        logger.info(f"Processing chat message: {user_input}")
        response = chat_about_movie(user_input, {"context": context})

        return jsonify({
            "response": response["text"],
            "context": response.get("context", context)
        })

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
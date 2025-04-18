import gradio as gr
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_welcome():
    """Returns the initial welcome message in the correct format"""
    return [{
        "role": "assistant",
        "content": "👋 Hi! I'm your movie expert chatbot. What's your favorite movie? I'd love to discuss it with you!"
    }]

def format_message(role: str, content: str) -> dict:
    """Convert message to the new messages format"""
    return {"role": "assistant" if role == "bot" else "user", "content": content}

def chat_with_movie_bot(user_input, history):
    # If no user input, keep existing history
    if not user_input:
        return history
    
    try:
        # Make request to Flask backend
        logger.debug(f"Sending request for movie: {user_input}")
        response = requests.post(
            "http://localhost:5000/recommend",
            json={"movie": user_input}
        )
        response.raise_for_status()
        
        # Extract response
        data = response.json()
        logger.debug(f"Received response: {data}")
        
        # Handle error responses
        if data.get("error"):
            return history + [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": "I encountered an error. Could you try again?"}
            ]
        
        # Extract message from response
        if "response" in data and isinstance(data["response"], dict):
            message = data["response"].get("text", "I couldn't understand the movie data. Could you try another one?")
        else:
            message = str(data.get("response", ""))
            
        return history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": message}
        ]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": "Sorry, I'm having trouble connecting to my movie database. Could you try again?"}
        ]
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": "I encountered an error. Could you try again?"}
        ]

# Create Gradio interface with chat layout
with gr.Blocks(theme=gr.themes.Soft()) as iface:
    with gr.Column(elem_classes=["container"]):
        gr.Markdown(
            "# 🎬 Movie Expert Chatbot",
            elem_classes=["centered-text"]
        )
        gr.Markdown(
            "Chat with me about movies! I'll help you explore films and discover new favorites.",
            elem_classes=["centered-text"]
        )
        
        chatbot = gr.Chatbot(
            value=show_welcome(),
            label="Chat History",
            height=500,
            container=True,
            type="messages",
            avatar_images=["👤", "🎬"],
            elem_classes=["chat-container"]
        )
        
        with gr.Row():
            with gr.Column(scale=4):
                msg = gr.Textbox(
                    label="Your message",
                    placeholder="Tell me your favorite movie or ask a question...",
                    show_label=False,
                    container=True
                )
            with gr.Column(scale=1):
                submit_btn = gr.Button("Send")
        
        clear = gr.ClearButton([msg, chatbot], value="Start New Chat")

        # Handle both button and enter key
        msg.submit(chat_with_movie_bot, inputs=[msg, chatbot], outputs=chatbot)
        submit_btn.click(chat_with_movie_bot, inputs=[msg, chatbot], outputs=chatbot)

        # Add example movies in a styled container
        with gr.Row(elem_classes=["examples-container"]):
            with gr.Column():
                gr.Examples(
                    examples=[
                        "Inception",
                        "The Matrix",
                        "Spirited Away",
                        "The Shawshank Redemption"
                    ],
                    inputs=msg
                )

if __name__ == "__main__":
    # Add custom CSS for centering and width control
    iface.css = """
        .container {
            max-width: 800px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding: 1rem !important;
        }
        .centered-text {
            text-align: center !important;
        }
        .chat-container {
            border-radius: 10px !important;
            margin-bottom: 1rem !important;
        }
        .examples-container {
            margin-top: 1rem !important;
            padding: 1rem !important;
            border-radius: 10px !important;
            background: rgba(0, 0, 0, 0.05) !important;
        }
    """
    iface.launch()
import gradio as gr
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovieChatbot:
    def __init__(self):
        self.context = None
        self.initialized = False

    def initialize_chat(self, movie_name):
        if not movie_name:
            return None, None, "Please enter a movie name"
        
        try:
            response = requests.post(
                "http://localhost:5000/initialize",
                json={"movie": movie_name}
            )
            data = response.json()
            
            if data.get("success"):
                self.context = data["context"]
                self.initialized = True
                initial_messages = [
                    (None, data["initial_response"]),
                    (None, data["recommendations"])
                ]
                return (
                    gr.update(visible=False),  # Hide movie input
                    gr.update(visible=True),   # Show chat interface
                    initial_messages,          # Show recommendations
                    ""                         # Clear error message
                )
            else:
                return None, None, None, f"Error: {data.get('error', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"Error initializing chat: {str(e)}")
            return None, None, None, f"Error: {str(e)}"
        
    def chat(self, message, history):
        if not message or not self.initialized:
            return history
        
        try:
            response = requests.post(
                "http://localhost:5000/chat",
                json={
                    "message": message,
                    "context": self.context
                }
            )
            data = response.json()
            
            if "error" in data:
                return history + [(message, f"Error: {data['error']}")]
            
            self.context = data.get("context", self.context)
            return history + [(message, data["response"])]
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return history + [(message, f"Error: {str(e)}")]

def create_interface():
    # Initialize chatbot instance
    chatbot = MovieChatbot()
    
    with gr.Blocks(theme=gr.themes.Soft()) as iface:
        with gr.Column():
            gr.Markdown("# Find Movies You'll Love 🎬")
        
        # Screen 1: Movie Input
        with gr.Column(visible=True) as movie_input_screen:
            gr.Markdown("### Type a movie you like, and we'll recommend similar ones!")
            movie_name = gr.Textbox(
                label="Movie Name",
                placeholder="E.g., Inception, The Dark Knight, Titanic...",
                container=False
            )
            submit_btn = gr.Button(
                "Find Similar Movies",
                size="lg",
                variant="primary"
            )
            error_msg = gr.Textbox(
                label="Status",
                interactive=False,
                visible=False
            )
            
            gr.Markdown(
                "*Try: Pulp Fiction, Avatar, Parasite*",
                elem_classes=["example-text"]
            )

        # Screen 2: Chat Interface
        with gr.Column(visible=False) as chat_screen:
            gr.Markdown("# Chat About These Movies 💬")
            chatbot_interface = gr.Chatbot(
                label="Movie Discussion",
                height=500,
                bubble_full_width=False,
            )
            with gr.Row():
                msg = gr.Textbox(
                    label="Your question",
                    placeholder="Ask me anything about these movies...",
                    scale=4
                )
                send_btn = gr.Button("💬", scale=1)
            
            gr.Markdown(
                "*Try: 'Which one has the best action scenes?' or 'Tell me more about the third recommendation'*",
                elem_classes=["example-text"]
            )
            
            new_chat_btn = gr.Button("↩ Start New Search", size="sm")

        # Handle movie input submission
            submit_btn.click(
                chatbot.initialize_chat,
                inputs=[movie_name],
                outputs=[movie_input_screen, chat_screen, chatbot_interface, error_msg]
            )

            # Handle chat messages
            msg.submit(chatbot.chat, inputs=[msg, chatbot_interface], outputs=chatbot_interface)
            send_btn.click(chatbot.chat, inputs=[msg, chatbot_interface], outputs=chatbot_interface)

            # Handle new chat button
            def reset_interface():
                chatbot.initialized = False
                chatbot.context = None
                return (
                    gr.update(visible=True),   # Show movie input
                    gr.update(visible=False),  # Hide chat
                    [],                        # Clear chat history
                    ""                         # Clear error message
                )

            new_chat_btn.click(
                reset_interface,
                outputs=[movie_input_screen, chat_screen, chatbot_interface, error_msg]
            )
        
        return iface

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(debug=True)
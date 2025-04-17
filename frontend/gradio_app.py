import gradio as gr
import requests

def chat_with_movie_bot(movie_name, history):
    if not movie_name:
        return history + [(None, "Please enter a movie name.")]
    
    try:
        # Make request to Flask backend
        response = requests.post(
            "http://localhost:5000/recommend",
            json={"movie": movie_name}
        )
        response.raise_for_status()
        
        # Extract response
        data = response.json()
        
        # Handle different response formats
        if "error" in data:
            return history + [(movie_name, f"Error: {data['error']}")]
        
        if isinstance(data["response"], dict):
            if "text" in data["response"]:
                message = data["response"]["text"]
            else:
                message = str(data["response"])
        else:
            message = str(data["response"])
            
        return history + [(movie_name, message)]
        
    except requests.exceptions.RequestException as e:
        return history + [(movie_name, f"Connection Error: {str(e)}")]
    except Exception as e:
        return history + [(movie_name, f"Error: {str(e)}")]

# Create Gradio interface with chat layout
with gr.Blocks(theme=gr.themes.Soft()) as iface:
    gr.Markdown("# 🎬 Movie Recommender Chatbot")
    gr.Markdown("Get movie recommendations and analysis by entering a movie name.")
    
    chatbot = gr.Chatbot(
        label="Chat History",
        height=400,
        bubble_full_width=False
    )
    
    with gr.Row():
        msg = gr.Textbox(
            label="Enter a movie name",
            placeholder="e.g. Inception",
            show_label=True,
            scale=4
        )
        submit_btn = gr.Button("Send", scale=1)
    
    clear = gr.ClearButton([msg, chatbot], value="Clear Chat")

    # Handle both button and enter key
    msg.submit(chat_with_movie_bot, inputs=[msg, chatbot], outputs=chatbot)
    submit_btn.click(chat_with_movie_bot, inputs=[msg, chatbot], outputs=chatbot)

    gr.Examples(
        examples=["Inception", "The Matrix", "Interstellar"],
        inputs=msg
    )

if __name__ == "__main__":
    iface.launch(debug=True)
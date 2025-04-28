from utils.tmdb_utils import search_movie, get_similar_movies, get_movie_details
from utils.comment_fetcher import fetch_all_reviews
from utils.opinion_mining import extract_themes_from_reviews
import chromadb
import openai
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# Initialize ChromaDB
chroma_client = chromadb.Client()
movie_collection = chroma_client.create_collection(
    name="movie_knowledge_base",
    metadata={"description": "Movie information, reviews, and analyses"}
)

def store_movie_data(movie_id, movie_details, reviews, analysis):
    """Store movie data in vector database"""
    # Create a unique document ID
    doc_id = f"movie_{movie_id}"
    
    # Combine all movie information into a single document
    movie_doc = {
        "title": movie_details["title"],
        "overview": movie_details["overview"],
        "genres": ", ".join(movie_details["genres"]),
        "director": movie_details["director"],
        "cast": ", ".join(movie_details["cast"]),
        "reviews": "\n".join([r["text"] for r in reviews]),
        "analysis": analysis
    }
    
    # Store in ChromaDB
    movie_collection.add(
        documents=[json.dumps(movie_doc)],
        metadatas=[{"movie_id": movie_id, "title": movie_details["title"]}],
        ids=[doc_id]
    )
    return doc_id

def query_movie_knowledge(query, n_results=3):
    """Query the vector database for relevant movie information"""
    results = movie_collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return [json.loads(doc) for doc in results["documents"][0]]

def generate_rag_response(query, relevant_info):
    """Generate response using RAG approach"""
    prompt = f"""
    As a movie expert chatbot, use the following movie information to answer the question:

    Relevant Movie Information:
    {json.dumps(relevant_info, indent=2)}

    User Query: {query}

    Provide a detailed response based on the available information. If specific information
    is not available in the context, acknowledge that limitation in your response.
    """
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def chat_about_movie(user_input, conversation_history=None):
    """Main chatbot function"""
    try:
        if conversation_history is None:
            # Initial movie search
            movie_id = search_movie(user_input)

            if not movie_id:
                return {"response": "Couldn't find the movie. Try another one."}

            # Gather movie information
            movie_details = get_movie_details(movie_id)
            reviews = fetch_all_reviews(movie_details["title"])
            analysis = extract_themes_from_reviews([r["text"] for r in reviews])
            
            # Store in vector database
            doc_id = store_movie_data(movie_id, movie_details, reviews, analysis)
            
            # Get similar movies
            similar_movies = get_similar_movies(movie_id)
            for similar in similar_movies[:3]:
                similar_reviews = fetch_all_reviews(similar["title"])
                similar_analysis = extract_themes_from_reviews([r["text"] for r in similar_reviews])
                store_movie_data(similar["id"], similar, similar_reviews, similar_analysis)

            # Get recommended movies
            similar_movies = get_similar_movies(movie_id)
            for similar in similar_movies[:3]:
                similar_reviews = fetch_all_reviews(similar["title"])
                similar_analysis = extract_themes_from_reviews([r["text"] for r in similar_reviews])
                store_movie_data(similar["id"], similar, similar_reviews, similar_analysis)
            
            # Format the analysis response
            analysis_json = json.loads(analysis)  # Parse the JSON string
            themes_response = (
                f"Analysis of {movie_details['title']} Reviews:\n\n"
                f"Emotional Tone: {analysis_json.get('Emotional Tone', 'N/A')}\n"
                f"Overall Sentiment: {analysis_json.get('Sentiment', 'N/A')}\n\n"
                f"Pros:\n- {'\n- '.join(analysis_json.get('Pros', []))}\n\n"
                f"Cons:\n- {'\n- '.join(analysis_json.get('Cons', []))}\n\n"
                f"Key Themes:\n- {'\n- '.join(analysis_json.get('Key Themes', []))}\n\n"
                f"Summary: {analysis_json.get('Summary', 'N/A')}\n"
                f"Sentiment Rating: {analysis_json.get('Sentiment rating', 'N/A')}/10"
            )
            
            return {
                "response": themes_response,
                "message": "You can ask me specific questions about these movies!",
                "movie_id": movie_id,
                "analysis": analysis  # Store analysis for future reference
            }
            
        else:
            # Handle follow-up questions
            relevant_info = query_movie_knowledge(user_input)
            response = generate_rag_response(user_input, relevant_info)
            return {"response": response}
            
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

if __name__ == "__main__":
    # Test conversation
    result = chat_about_movie("Inception")
    print("Initial Analysis:", result["response"])
    print(result["message"])

    # Test follow-up questions
    follow_up_questions = [
        "What are the main themes of this movie?",
        "How do viewers rate this movie?",
        "What are similar movies I might enjoy?"
    ]

    for question in follow_up_questions:
        response = chat_about_movie(question, {"movie_id": result["movie_id"]})
        print(f"\nQ: {question}")
        print(f"A: {response['response']}")
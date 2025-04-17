from utils.tmdb_utils import search_movie, get_similar_movies
from utils.reddit_scraper import fetch_reddit_comments
from utils.opinion_mining import extract_themes_from_reviews
import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_rag_response(query, context, movie_title):
    prompt = f"""
        As a movie expert chatbot, use the following movie analysis data to answer the question:

        Main Movie: {movie_title}
        Analysis Context: {context}

        User Query: {query}

        Provide a detailed response based only on the available analysis data.
    """
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def chat_about_movie(user_input, conversation_history=None):
    if conversation_history is None:
        # Initial movie search and analysis
        movie = search_movie(user_input)
        if not movie:
            return "Couldn't find the movie. Try another one.", None

        # Build knowledge base
        movie_analyses = {}
        similar_movies = get_similar_movies(movie["id"])
        
        # Analyze main movie
        reviews = fetch_reddit_comments(movie["title"])
        main_movie_analysis = extract_themes_from_reviews(reviews)

        # Analyze similar movies
        for similar_title in similar_movies[:3]:
            similar_reviews = fetch_reddit_comments(similar_title)
            if similar_reviews:
                analysis = extract_themes_from_reviews(similar_reviews)
                movie_analyses[similar_title] = analysis

        # Initial recommendation response
        context = {
            "main_movie": movie["title"],
            "main_analysis": main_movie_analysis,
            "similar_movies": movie_analyses
        }

        initial_prompt = f"""
            Based on the analysis of {movie['title']} and similar movies, provide a brief overview 
            and recommendations. Focus on thematic connections and similar viewing experiences.
        """
        recommendation = generate_rag_response(initial_prompt, context, movie["title"])
        
        return {
            "response": recommendation,
            "context": context,
            "message": "You can ask me specific questions about these movies or request more details!"
        }
    else:
        # Handle follow-up questions using RAG
        return generate_rag_response(
            user_input,
            conversation_history["context"],
            conversation_history["context"]["main_movie"]
        )

if __name__ == "__main__":
    # Initial conversation
    result = chat_about_movie("Inception")
    print("Initial Analysis:", result["response"])
    print(result["message"])

    # Example follow-up questions using RAG
    follow_up_questions = [
        "What are the main themes shared between these movies?",
        "Which movie has the most positive audience reception?",
        "Compare the visual effects in these movies"
    ]

    for question in follow_up_questions:
        response = chat_about_movie(question, result)
        print(f"\nQ: {question}")
        print(f"A: {response}")
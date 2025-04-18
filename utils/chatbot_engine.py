from utils.tmdb_utils import search_movie, get_similar_movies, get_movie_details, get_recommendations_by_genres
from utils.reddit_scraper import fetch_reddit_comments
from utils.opinion_mining import extract_themes_from_reviews
from utils.vector_store import MovieVectorStore
import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.Client(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# Initialize vector store
vector_store = MovieVectorStore()

def generate_rag_response(query, context, movie_title):
    # Use vector search for enhanced context
    search_results = vector_store.search(query, k=2)
    
    # Create a concise context that focuses on what's relevant to the query
    focused_context = {
        "main_movie": movie_title,
        "main_analysis": context.get("main_analysis", ""),
        "movie_details": context.get("movie_details", {}),
        "similar_movies": context.get("similar_movies", {}),
        "additional_recommendations": context.get("additional_recommendations", {}),
        "relevant_context": [
            {"title": result[1]["title"], "analysis": result[1]["analysis"]}
            for result in search_results
            if result[1]["title"].lower() != movie_title.lower()
        ]
    }

    # For follow-up recommendations, ensure we don't repeat previous suggestions
    if "more detailed recommendations" in query.lower():
        prompt = f"""
            Let's explore more great movies similar to {movie_title}! Focus on different aspects:

            1. If we previously focused on similar plots, now highlight movies with similar themes or visual style
            2. If we discussed sci-fi elements, now highlight movies with similar world-building or character development
            3. Suggest 2-3 NEW recommendations (different from previous ones) and explain WHY they're great matches
            4. End with a specific question about which aspect (themes, style, characters, etc.) the user enjoys most

            Previous Recommendations: {list(context.get('similar_movies', {}).keys())}
            Movie Details: {focused_context['movie_details']}
            Analysis: {focused_context['main_analysis']}

            Keep it engaging and conversational!
        """
    elif "Give a brief, exciting introduction" in query:
        prompt = f"""
            As a movie recommendation expert, create an engaging response about {movie_title}.
            Structure your response as follows:

            1. A brief, exciting description of the movie (2 sentences max)
            2. Mention its genres: {focused_context['movie_details'].get('genres', [])}
            3. One standout feature that makes this movie special
            4. Suggest 2-3 similar movies based on these genres and themes, explaining WHY you recommend each one
            5. End with an engaging question like:
               - "Would you like to know more about any of these recommendations?"
               - "Shall we explore more movies in the [specific genre] genre?"
               - "What aspects of these movies interest you the most?"

            Available Context:
            Movie Details: {focused_context['movie_details']}
            Analysis: {focused_context['main_analysis']}
            Similar Movies: {focused_context['similar_movies']}

            Keep it conversational and enthusiastic!
        """
    else:
        prompt = f"""
            As a movie recommendation expert, address this specific question about {movie_title}.
            After answering their question:

            1. Connect their interest to a specific genre or theme
            2. Suggest 1-2 relevant movies that match this specific interest
            {
                "3. If discussing a specific genre, recommend top-rated movies in that genre:\\n" +
                "   " + "\\n   ".join([f"- {title}" for title in focused_context.get("genre_recommendations", {}).keys()])
                if "genre_recommendations" in focused_context else
                "3. Ask if they'd like to explore more movies with similar " + 
                (focused_context['movie_details'].get('genres', ['themes'])[0] if focused_context['movie_details'].get('genres') else "themes")
            }

            Available Context:
            Movie Details: {focused_context['movie_details']}
            Analysis: {focused_context['main_analysis']}
            Similar Movies: {focused_context['similar_movies']}
            {
                "Genre Recommendations: " + str(focused_context['genre_recommendations'])
                if "genre_recommendations" in focused_context else ""
            }
            User Query: {query}

            Keep it conversational and focus on making personalized recommendations!
        """
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def chat_about_movie(user_input, conversation_history=None):
    # Handle short responses and affirmatives
    if conversation_history and len(user_input.strip()) <= 4:
        lower_input = user_input.lower().strip()
        if lower_input in ['yes', 'y', 'sure', 'ok', 'yeah']:
            # User wants to know more about previous recommendations
            main_movie = conversation_history["context"]["main_movie"]
            return {
                "text": generate_rag_response(
                    f"Provide more detailed recommendations for movies similar to {main_movie}, focusing on different aspects than previously mentioned",
                    conversation_history["context"],
                    main_movie
                ),
                "context": conversation_history["context"]
            }
    
    # Handle follow-up requests for more recommendations
    if conversation_history and any(keyword in user_input.lower() for keyword in ["more", "similar", "like"]):
        main_movie = conversation_history["context"]["main_movie"]
        movie_details = conversation_history["context"]["movie_details"]
        
        # Get additional genre-based recommendations
        genre_ids = get_genre_ids(movie_details.get("genres", []))
        additional_recommendations = get_recommendations_by_genres(genre_ids, exclude_movie_id=movie_details["id"])
        
        # Update context with new recommendations
        updated_context = conversation_history["context"].copy()
        updated_context["additional_recommendations"] = {
            m["title"]: {
                "genres": m["genres"],
                "overview": m["overview"],
                "rating": m["vote_average"]
            } for m in additional_recommendations
        }
        
        # Generate response focusing on new recommendations
        response_text = generate_rag_response(
            f"Suggest more movies similar to {main_movie} with detailed explanations",
            updated_context,
            main_movie
        )
        
        return {"text": response_text, "context": updated_context}

    if conversation_history is None:
        # Check if movie already exists in vector store
        existing_data = vector_store.get_movie_by_title(user_input)
        if existing_data:
            response_text = generate_rag_response(
                "Give a brief, exciting introduction to this movie",
                existing_data["analysis"],
                existing_data["title"]
            )
            return {"text": response_text, "context": existing_data["analysis"]}

        # If not in vector store, fetch new data
        movie = search_movie(user_input)
        if not movie:
            return {"text": "I couldn't find that movie. Could you try another one?", "context": None}

        try:
            # Get similar movies and details
            similar_movies = get_similar_movies(movie["id"])
            
            # Analyze main movie
            reviews = fetch_reddit_comments(movie["title"])
            main_movie_analysis = extract_themes_from_reviews(reviews) if reviews else "No reviews found yet."

            # Get movie details
            movie_details = get_movie_details(movie["id"])

            # Store context
            context = {
                "main_movie": movie["title"],
                "main_analysis": main_movie_analysis,
                "movie_details": movie_details,
                "similar_movies": {
                    m["title"]: {
                        "genres": m.get("genres", []),
                        "overview": m.get("overview", ""),
                        "rating": m.get("vote_average", 0)
                    } for m in similar_movies
                }
            }

            # Store in vector database
            vector_store.add_movie(movie["title"], context)

            # Generate initial response
            response_text = generate_rag_response(
                "Give a brief, exciting introduction to this movie",
                context,
                movie["title"]
            )
            
            return {"text": response_text, "context": context}
            
        except Exception as e:
            print(f"Error processing movie data: {str(e)}")
            return {"text": "I encountered an error while analyzing this movie. Could you try again?", "context": None}
    else:
        # Handle follow-up questions using RAG with vector search
        return {
            "text": generate_rag_response(
                user_input,
                conversation_history["context"],
                conversation_history["context"]["main_movie"]
            ),
            "context": conversation_history["context"]
        }

def get_genre_ids(genre_names):
    # Common TMDB genre IDs
    genre_map = {
        "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
        "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
        "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
        "mystery": 9648, "romance": 10749, "science fiction": 878,
        "sci-fi": 878, "thriller": 53, "war": 10752, "western": 37
    }
    return [genre_map[g.lower()] for g in genre_names if g.lower() in genre_map]

if __name__ == "__main__":
    # Initial conversation
    result = chat_about_movie("Inception")
    print("Initial Analysis:", result["text"])

    # Example follow-up questions using RAG
    follow_up_questions = [
        "What are the main themes shared between these movies?",
        "Which movie has the most positive audience reception?",
        "Compare the visual effects in these movies"
    ]

    for question in follow_up_questions:
        response = chat_about_movie(question, result)
        print(f"\nQ: {question}")
        print(f"A: {response['text']}")
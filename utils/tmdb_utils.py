import requests, os
from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def get_movie_details(movie_id):
    """Get comprehensive movie details including credits and keywords"""
    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,keywords,recommendations,watch/providers"
    res = requests.get(details_url).json()
    
    # Extract relevant information
    return {
        "id": res.get("id"),
        "title": res.get("title"),
        "genres": [genre["name"] for genre in res.get("genres", [])],
        "release_date": res.get("release_date"),
        "runtime": res.get("runtime"),
        "overview": res.get("overview"),
        "imdb_rating": res.get("vote_average"),
        "keywords": [kw["name"] for kw in res.get("keywords", {}).get("keywords", [])],
        "director": next((crew["name"] for crew in res.get("credits", {}).get("crew", []) 
                        if crew["job"] == "Director"), None),
        "cast": [cast["name"] for cast in res.get("credits", {}).get("cast", [])[:5]],
        "watch_providers": res.get("watch/providers", {}).get("results", {}).get("US", {}),
        "popularity": res.get("popularity"),
        "original_language": res.get("original_language")
    }

def search_movie(query):
    url = f"https://api.themoviedb.org/3/search/movie?query={query}&api_key={TMDB_API_KEY}"
    res = requests.get(url).json()
    if not res['results']:
        return None
    
    # Get full details for the first result
    movie_basic = res['results'][0]
    return movie_basic['id']

def get_similar_movies(movie_id, limit=5):
    """Get similar movies with detailed information"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar?api_key={TMDB_API_KEY}"
    res = requests.get(url).json()
    
    similar_movies = []
    for movie in res['results'][:limit]:
        details = get_movie_details(movie['id'])
        similar_movies.append(details)
    
    return similar_movies

def get_recommended_movies(movie_id, limit=5):
    """Get recommended movies from TMDB"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?api_key={TMDB_API_KEY}"
    res = requests.get(url).json()
    
    recommended_movies = []
    for movie in res.get('results', [])[:limit]:
        details = get_movie_details(movie['id'])
        recommended_movies.append(details)
    
    return recommended_movies

# Update the main block to include recommendations
if __name__ == "__main__":
    query = input("Enter movie name: ")
    movie_id = search_movie(query)
    if movie_id:
        movie_details = get_movie_details(movie_id)
        print("\nMovie Details:")
        for key, value in movie_details.items():
            print(f"{key}: {value}")
        
        print("\nSimilar Movies:")
        similar_movies = get_similar_movies(movie_id)
        for similar in similar_movies:
            print(f"\n{similar['title']}:")
            print(f"Genres: {', '.join(similar['genres'])}")
            print(f"Rating: {similar['imdb_rating']}")
            print(f"Original Language: {similar['original_language']}")
            print("-" * 50)
            
        print("\nRecommended Movies:")
        recommended_movies = get_recommended_movies(movie_id)
        for recommended in recommended_movies:
            print(f"\n{recommended['title']}:")
            print(f"Genres: {', '.join(recommended['genres'])}")
            print(f"Rating: {recommended['imdb_rating']}")
            print(f"Original Language: {recommended['original_language']}")
            print("-" * 50)
    else:
        print("Movie not found.")
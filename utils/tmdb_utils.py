import os
import requests
from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def search_movie(query):
    url = f"https://api.themoviedb.org/3/search/movie?query={query}&api_key={TMDB_API_KEY}"
    try:
        response = requests.get(url)
        res = response.json()
        return res['results'][0] if res.get('results') else None
    except Exception as e:
        print(f"Error in TMDB API call: {str(e)}")
        return None

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,keywords"
    try:
        res = requests.get(url).json()
        return {
            'id': res.get('id'),
            'title': res.get('title'),
            'overview': res.get('overview'),
            'genres': [genre['name'] for genre in res.get('genres', [])],
            'release_date': res.get('release_date'),
            'vote_average': res.get('vote_average'),
            'director': next((crew['name'] for crew in res.get('credits', {}).get('crew', []) if crew['job'] == 'Director'), None),
            'cast': [cast['name'] for cast in res.get('credits', {}).get('cast', [])[:5]],
            'keywords': [kw['name'] for kw in res.get('keywords', {}).get('keywords', [])]
        }
    except Exception as e:
        print(f"Error getting movie details: {str(e)}")
        return None

def get_similar_movies(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar?api_key={TMDB_API_KEY}"
    try:
        res = requests.get(url).json()
        similar_movies = []
        for movie in res.get('results', [])[:5]:  # Limit to top 5 similar movies
            details = get_movie_details(movie['id'])
            if details:
                similar_movies.append(details)
        return similar_movies
    except Exception as e:
        print(f"Error getting similar movies: {str(e)}")
        return []

def get_recommendations_by_genres(genres, exclude_movie_id=None):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={','.join(str(g) for g in genres)}&sort_by=vote_average.desc"
    try:
        res = requests.get(url).json()
        recommendations = []
        for movie in res.get('results', []):
            if movie['id'] != exclude_movie_id and len(recommendations) < 3:
                details = get_movie_details(movie['id'])
                if details:
                    recommendations.append(details)
        return recommendations
    except Exception as e:
        print(f"Error getting genre recommendations: {str(e)}")
        return []

if __name__ == "__main__":
    query = input("Enter movie name: ")
    movie = search_movie(query)
    if movie:
        print(f"Movie found: {movie['title']}")
        details = get_movie_details(movie['id'])
        if details:
            print(f"\nDetails for {details['title']}:")
            print(f"Director: {details['director']}")
            print(f"Genres: {', '.join(details['genres'])}")
            print(f"Cast: {', '.join(details['cast'])}")
            print("\nSimilar movies:")
            for similar in get_similar_movies(movie['id']):
                print(f"- {similar['title']} ({similar.get('release_date', 'N/A')})")
import requests, os
from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def search_movie(query):
    url = f"https://api.themoviedb.org/3/search/movie?query={query}&api_key={TMDB_API_KEY}"
    res = requests.get(url).json()
    return res['results'][0] if res['results'] else None

def get_similar_movies(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar?api_key={TMDB_API_KEY}"
    res = requests.get(url).json()
    return [m['title'] for m in res['results']]

if __name__ == "__main__":
    query = input("Enter movie name: ")
    movie = search_movie(query)
    if movie:
        print(f"Movie found: {movie['title']}")
        similar_movies = get_similar_movies(movie['id'])
        print("Similar movies:")
        for m in similar_movies:
            print(m)
    else:
        print("Movie not found.")
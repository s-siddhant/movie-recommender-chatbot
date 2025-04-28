import praw
import requests
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def fetch_tmdb_reviews(movie_name, limit=3):
    """Fetch movie reviews from TMDB"""
    try:
        # First search for the movie to get its ID
        search_url = f"https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": movie_name
        }
        search_response = requests.get(search_url, params=params).json()
        
        if not search_response.get("results"):
            logger.warning(f"No movie found on TMDB for: {movie_name}")
            return []
            
        movie_id = search_response["results"][0]["id"]
        
        # Fetch reviews for the movie
        reviews_url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "page": 1
        }
        
        reviews_response = requests.get(reviews_url, params=params).json()
        reviews = []
        
        for review in reviews_response.get("results", [])[:limit]:
            reviews.append({
                "text": review.get("content", ""),
                "author": review.get("author", "Anonymous"),
                "rating": review.get("author_details", {}).get("rating", 0),
                "date": review.get("created_at", ""),
                "source": "TMDB"
            })
            
        logger.info(f"Found {len(reviews)} TMDB reviews for {movie_name}")
        return reviews
        
    except Exception as e:
        logger.error(f"Error fetching TMDB reviews for {movie_name}: {str(e)}")
        return []

def fetch_reddit_comments(movie_name, limit=5):
    """Fetch movie discussions from Reddit"""
    try:
        # Search for movie discussions in r/movies
        subreddit = reddit.subreddit("movies")
        search_query = f"{movie_name} discussion"
        submissions = subreddit.search(search_query, sort="relevance", limit=2)
        
        reviews = []
        for submission in submissions:
            submission.comments.replace_more(limit=0)  # Flatten comment tree
            for comment in submission.comments[:limit]:
                if len(comment.body) > 5:  # Filter out short comments
                    reviews.append({
                        "text": comment.body,
                        "author": str(comment.author),
                        "rating": None,  # Reddit comments don't have ratings
                        "date": datetime.fromtimestamp(comment.created_utc).strftime("%Y-%m-%d"),
                        "source": "Reddit",
                        "score": comment.score
                    })
                    
        logger.info(f"Found {len(reviews)} Reddit comments for {movie_name}")
        return reviews
        
    except Exception as e:
        logger.error(f"Error fetching Reddit comments for {movie_name}: {str(e)}")
        return []

def fetch_all_reviews(movie_name, limit=5):
    """Fetch reviews from both TMDB and Reddit"""
    tmdb_reviews = fetch_tmdb_reviews(movie_name, limit)
    reddit_reviews = fetch_reddit_comments(movie_name, limit)
    
    all_reviews = tmdb_reviews + reddit_reviews
    return all_reviews

if __name__ == "__main__":
    movie_name = input("Enter movie name: ")
    reviews = fetch_all_reviews(movie_name)
    
    if reviews:
        print(f"\nReviews for {movie_name}:")
        for i, review in enumerate(reviews, 1):
            print(f"\nReview #{i} ({review['source']})")
            print(f"Author: {review['author']}")
            print(f"Date: {review['date']}")
            print(f"Text: {review['text'][:500]}...")  # Truncate long reviews
            print("-" * 50)
    else:
        print("No reviews found.")
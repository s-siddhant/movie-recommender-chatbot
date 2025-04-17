import praw, os
from dotenv import load_dotenv

load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

def fetch_reddit_comments(movie_name, limit=10):  # Reduced limit
    comments = []
    try:
        # Limit search to top posts
        search_query = f"title:{movie_name}"
        posts = list(reddit.subreddit("movies").search(
            search_query, 
            limit=limit, 
            sort='relevance'
        ))

        # Process only top 5 posts
        for post in posts[:5]:
            top_comments = list(post.comments)[:5]  # Get only first 2 top-level comments
            comments.extend([comment.body for comment in top_comments if hasattr(comment, 'body')])

        return comments[:10]  # Return max 10 comments
    except Exception as e:
        print(f"Error fetching comments for {movie_name}: {str(e)}")
        return []

if __name__ == "__main__":  
    movie_name = input("Enter movie name: ")
    comments = fetch_reddit_comments(movie_name)
    if comments:
        print(f"Comments for {movie_name}:")
        for comment in comments:
            print(comment)
    else:
        print("No comments found.")
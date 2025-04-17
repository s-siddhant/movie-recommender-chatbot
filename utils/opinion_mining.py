import openai, os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

def extract_themes_from_reviews(reviews):
    joined = "\n".join(reviews)
    prompt = f"""
You're a movie analysis expert. Analyze these reviews and provide a structured analysis with the following:

Reviews to analyze:
{joined}

Please provide analysis in this format:
1. Emotional Tone: Overall emotional response of viewers (positive/negative/mixed)
2. Pros: List 2-3 most praised elements
3. Cons: List 2-3 most criticized elements
4. Key Themes: 2-3 recurring themes or patterns
5. Summary: 2-3 sentence overview
6. Overall Rating: Estimate average rating out of 10 based on sentiment

Format the response with clear headers and bullet points.
"""
    res = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

if __name__ == "__main__":
    reviews = [
        "The acting was phenomenal, especially the lead actor.",
        "I loved the cinematography and the pacing was perfect.",
        "The story was a bit slow but the visuals made up for it.",
        "The soundtrack was hauntingly beautiful.",
        "The character development was weak, but the action scenes were thrilling."
    ]
    analysis = extract_themes_from_reviews(reviews)
    print("\nDetailed Movie Analysis:")
    print(analysis)
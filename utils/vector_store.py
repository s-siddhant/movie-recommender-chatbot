import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os
from typing import Dict, List, Tuple

class MovieVectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.encoder = SentenceTransformer(model_name)
        self.dimension = 384  # Default dimension for the chosen model
        self.index = faiss.IndexFlatL2(self.dimension)
        self.movie_data: Dict[int, dict] = {}
        self.load_if_exists()

    def load_if_exists(self):
        if os.path.exists('movie_vectors.faiss'):
            self.index = faiss.read_index('movie_vectors.faiss')
            with open('movie_data.pkl', 'rb') as f:
                self.movie_data = pickle.load(f)

    def save(self):
        faiss.write_index(self.index, 'movie_vectors.faiss')
        with open('movie_data.pkl', 'wb') as f:
            pickle.dump(self.movie_data, f)

    def add_movie(self, movie_title: str, analysis: dict):
        # Create a comprehensive text representation of the movie data
        text = f"{movie_title}. {analysis.get('main_analysis', '')}. "
        if 'similar_movies' in analysis:
            for movie, movie_analysis in analysis['similar_movies'].items():
                text += f"Similar movie {movie}: {movie_analysis}. "
        
        # Generate embedding
        embedding = self.encoder.encode([text])[0]
        
        # Add to FAISS index
        index_id = self.index.ntotal
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # Store movie data
        self.movie_data[index_id] = {
            'title': movie_title,
            'analysis': analysis
        }
        
        self.save()
        return index_id

    def search(self, query: str, k: int = 3) -> List[Tuple[float, dict]]:
        # Generate query embedding
        query_vector = self.encoder.encode([query])[0]
        
        # Search in FAISS
        distances, indices = self.index.search(np.array([query_vector], dtype=np.float32), k)
        
        # Return results with distances and full movie data
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx in self.movie_data:  # -1 indicates no result found
                results.append((float(dist), self.movie_data[idx]))
        
        return results

    def get_movie_by_title(self, title: str) -> dict:
        for movie_data in self.movie_data.values():
            if movie_data['title'].lower() == title.lower():
                return movie_data
        return None
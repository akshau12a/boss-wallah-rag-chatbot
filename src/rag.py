# src/rag.py
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .utils import normalize_languages_field
import os

# Try to import Gemini SDK safely
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

REQUIRED_INPUT_COLUMNS = [
    "Course No",
    "Course Title",
    "Course Description",
    "Released Languages",
    "Who This Course is For",
]

CANONICAL_COLUMNS = {
    "Course Title": "Course Title",
    "Course Description": "About Course",
    "Released Languages": "Course Released Languages",
    "Who This Course is For": "Who This Course Is For",
}

@dataclass
class Hit:
    course_title: str
    about: str
    who_for: str
    languages: set
    score: float

class RAGIndex:
    def __init__(self, df: pd.DataFrame):
        # validate columns
        for col in REQUIRED_INPUT_COLUMNS:
            if col not in df.columns:
                raise ValueError(f"Dataset missing required column: {col}")

        # rename to canonical
        df = df.rename(columns=CANONICAL_COLUMNS)

        # parse languages
        df["__languages"] = df["Course Released Languages"].apply(normalize_languages_field)

        # build searchable text
        df["__text"] = (
            df["Course Title"].fillna("").astype(str) + " \n" +
            df["About Course"].fillna("").astype(str) + " \n" +
            df["Who This Course Is For"].fillna("").astype(str)
        )

        self.df = df
        # default vectorizer (no stop_words → preserves Indian language tokens)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95)
        self.matrix = self.vectorizer.fit_transform(self.df["__text"])

    @staticmethod
    def from_excel(path: str) -> "RAGIndex":
        df = pd.read_excel(path)
        return RAGIndex(df)

    def search(self, query: str, k: int = 5, lang_filter: Optional[str] = None) -> List[Hit]:
        vec = self.vectorizer.transform([query])
        sims = cosine_similarity(vec, self.matrix)[0]
        self.df["__score"] = sims
        df_sorted = self.df.sort_values("__score", ascending=False)

        if lang_filter:
            df_sorted = df_sorted[df_sorted["__languages"].apply(lambda s: lang_filter in s)]

        top = df_sorted.head(k)
        hits: List[Hit] = []
        for _, row in top.iterrows():
            hits.append(Hit(
                course_title=row["Course Title"],
                about=row["About Course"],
                who_for=row["Who This Course Is For"],
                languages=row["__languages"],
                score=float(row["__score"]),
            ))
        return hits

    def filter_by_language(self, lang_name: str, k: int = 100) -> List[Hit]:
        return self.search(query="", k=k, lang_filter=lang_name)

    # ---------------- Gemini-powered response ---------------- #
    def gemini_answer(self, query: str, k: int = 5, model: str = "gemini-1.5-flash") -> str:
        """
        Generate a grounded answer using Gemini, restricted to dataset hits.
        """
        if not GEMINI_AVAILABLE:
            return "❌ Gemini SDK not installed. Please add `google-generativeai` to requirements."

        # Step 1: Retrieve top matches
        hits = self.search(query, k=k)

        if not hits:
            return "I couldn't find any relevant courses in the dataset."

        # Step 2: Build context
        context = "\n\n".join(
            f"Course Title: {h.course_title}\nAbout: {h.about}\nWho For: {h.who_for}\nLanguages: {', '.join(h.languages)}"
            for h in hits
        )

        # Step 3: Ask Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "❌ GOOGLE_API_KEY not set in environment variables."
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model)
            prompt = f"""
            You are Boss Wallah's course support assistant.
            The following are relevant courses from the dataset:

            {context}

            Question: {query}

            Answer the question strictly based only on the dataset above.
            If the answer is not in the dataset, say you don't know.
            """

            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"❌ Gemini error: {e}"
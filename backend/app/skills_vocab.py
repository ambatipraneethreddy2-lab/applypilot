"""A shared skills vocabulary + alias map.

Used for two things:
1. Normalising skill names so "JS", "Javascript" and "JavaScript" count as the
   same skill when we compare a resume to a job (LLMs are inconsistent here).
2. Powering the offline "mock" LLM provider so the app works without an API key.
"""
import re

ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "reactjs": "react",
    "react.js": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "llm": "llms",
    "large language models": "llms",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "rest": "rest apis",
    "rest api": "rest apis",
    "restful apis": "rest apis",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "hugging face": "huggingface",
    "golang": "go",
    "c sharp": "c#",
    "vector db": "vector databases",
    "vector database": "vector databases",
    "retrieval augmented generation": "rag",
    "retrieval-augmented generation": "rag",
}

KNOWN_SKILLS: list[str] = [
    # languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "sql", "r", "scala", "kotlin", "swift",
    # web
    "react", "angular", "vue", "next.js", "node.js", "express", "html", "css", "tailwind", "redux",
    "fastapi", "django", "flask", "spring boot", "rest apis", "graphql",
    # data / ml
    "machine learning", "deep learning", "natural language processing", "computer vision",
    "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "huggingface",
    "llms", "generative ai", "rag", "langchain", "llamaindex", "prompt engineering", "fine-tuning",
    "embeddings", "vector databases", "pgvector", "pinecone", "openai api", "mlops", "statistics",
    "data analysis", "spark", "airflow", "tableau", "power bi",
    # infra
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "linux", "git", "ci/cd",
    "github actions", "jenkins", "postgresql", "mysql", "mongodb", "redis", "kafka",
    # practices
    "microservices", "system design", "unit testing", "agile", "data structures", "algorithms",
]


def normalize_skill(skill: str) -> str:
    s = skill.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return ALIASES.get(s, s)


def find_known_skills(text: str) -> list[str]:
    """Return known skills that appear in the text (word-boundary match), incl. aliases."""
    lowered = " " + text.lower() + " "
    found: list[str] = []

    def present(term: str) -> bool:
        # (?<![\w]) / (?![\w]) instead of \b so terms like "c++" and "node.js" work
        return re.search(r"(?<![\w])" + re.escape(term) + r"(?![\w+#])", lowered) is not None

    for skill in KNOWN_SKILLS:
        if skill in {"r", "go"}:  # too ambiguous in plain English ("go", "R&D"); "golang" still matches
            continue
        if present(skill) and skill not in found:
            found.append(skill)
    for alias, canonical in ALIASES.items():
        if canonical in KNOWN_SKILLS and canonical not in found and len(alias) > 2 and present(alias):
            found.append(canonical)
    return found

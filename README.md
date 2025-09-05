#  Boss Wallah — Courses Support Chatbot

##  Overview
This project is a **Retrieval-Augmented Generation (RAG)** based chatbot designed to support users by answering questions about agricultural, business, and personal finance courses from **Boss Wallah**.  

It uses a curated dataset of **100 courses** and provides ChatGPT-like conversational answers **strictly based on the dataset**, with additional support for **language-specific queries** and **bonus practical questions**.

---

##  Features
- **Dataset-driven answers** → Queries are answered using semantic search over the dataset (`bw_courses.xlsx`).
- **Multi-language support** → Answers consider course availability in:
  - Hindi, Kannada, Malayalam, Tamil, Telugu, English
- **Natural conversational style** → Responses are summarized for readability.
- **Bonus category support**:
  - Dairy farm queries (e.g., *“How many cows are needed to start a dairy farm?”*).
  - Nearby seed store lookup near **Whitefield, Bangalore** (via Google Places API or OpenStreetMap).
- **Demo prompts & chat history** → Sidebar includes sample prompts.
- **Robust fallback** → If query isn’t found, informative messages appear in the **user’s detected language**.

---

##  Project Structure
boss-wallah-rag-chatbot/
├─ app.py # Main Streamlit app (UI + logic)
├─ requirements.txt # Dependencies
├─ .env # API keys (GOOGLE_API_KEY required)
├─ data/
│ └─ bw_courses.xlsx # Dataset of Boss Wallah courses
├─ src/
│ ├─ rag.py # RAG indexing & search logic
│ ├─ utils.py # Language detection & helpers
│ └─ agent.py # External agent for store lookup
├─ README.md # Documentation


---

##  Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone <repo-url>
cd boss-wallah-rag-chatbot
```
## Create a virtual environment & install dependencies

python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt

## Configure environment variables

GOOGLE_API_KEY=your_google_api_key_here

## Run the chatbot
streamlit run app.py

### Key Components
# app.py

Streamlit-based user interface.

Loads and caches RAG index from Excel dataset.

Handles query routing (dataset search, bonus dairy farm answers, or store lookup).

Displays responses in conversational style.

# src/rag.py

Builds TF-IDF vectorizer-based search index.

Provides semantic search & language filtering.

Returns structured results.

# src/utils.py

Detects user query language (langdetect).

Normalizes dataset language fields.

Provides localized out-of-scope messages.

# src/agent.py

Finds seed stores near Whitefield using:

Google Places API, or

OpenStreetMap Overpass API (fallback).


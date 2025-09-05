import os
import streamlit as st
from dotenv import load_dotenv
from src.rag import RAGIndex
from src.utils import detect_language_name, OUT_OF_SCOPE, query_requests_language_filter
from src.agent import find_seed_stores_near_whitefield

st.set_page_config(page_title="Boss Wallah — Courses Support Bot", page_icon="🧠", layout="wide")
load_dotenv()

st.title(" Boss Wallah — Courses Support Chatbot")
st.caption("Ask about our courses in agriculture, business, and personal finance")

@st.cache_resource(show_spinner=False)
def load_index():
    from pathlib import Path
    data_path = Path("data/bw_courses.xlsx")
    if not data_path.exists():
        st.error(f"Dataset not found: {data_path}")
        return None
    try:
        return RAGIndex.from_excel(str(data_path))
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return None

index = load_index()
if index is None:
    st.stop()

def format_courses_response(hits, query, lang_filter=None):
    if not hits:
        return "Sorry, I couldn't find any relevant courses for your query."
    if lang_filter:
        reply = f"Yes, here are our courses available in {lang_filter}:\n"
        reply += '\n'.join([f"- {h.course_title}" for h in hits[:10]])
        if len(hits) > 10:
            reply += "\n...and more!"
        return reply

    # If it's a single course match (e.g.: "Tell me about honey bee farming course")
    if len(hits) == 1 or "about" in query.lower() or "tell me" in query.lower():
        h = hits[0]
        reply = (
            f"**{h.course_title}**\n\n"
            f"{h.about}\n\n"
            f"*Who this course is for*: {h.who_for}\n\n"
            f"*Available in*: {', '.join(sorted(h.languages))}."
        )
        return reply

    # For multi-match, topic-style queries
    reply = "Here are some courses relevant to your question:\n"
    for h in hits[:5]:
        reply += (
            f"\n**{h.course_title}**\n"
            f"{h.about}\n"
            f"*Languages*: {', '.join(sorted(h.languages))}\n"
        )
    if len(hits) > 5:
        reply += "\nLet me know if you want more details about any course."
    return reply

# DAIRY FARM PRACTICAL ANSWERS — edit as needed for your region
DAIRY_FARM_INFO = {
    "English": (
        "To start a small-scale dairy farm in India, most experts recommend beginning with 10 to 15 cows. "
        "This allows for manageable operations while still being profitable. Our courses can guide you on "
        "detailed setup, animal care, and business planning."
    ),
    "Hindi": (
        "भारत में छोटे स्तर की डेयरी फार्म शुरू करने के लिए आमतौर पर 10 से 15 गायें रखना उचित है। "
        "इससे व्यवसाय प्रबंधनीय और लाभकारी रहता है। हमारे कोर्स में आपको डीटेल प्लानिंग, देखभाल और बिजनेस सेटअप की जानकारी मिलेगी।"
    ),
    "Kannada": (
        "ಭಾರತದಲ್ಲಿ ಸಣ್ಣ ಮಟ್ಟದ ಡೇರಿ ಫಾರ್ಮ್ ಪ್ರಾರಂಭಿಸಲು ಸಾಮಾನ್ಯವಾಗಿ 10 ರಿಂದ 15 ಗೋವುಗಳನ್ನು ಹೊಂದುವಂತೆ ಶಿಫಾರಸು ಮಾಡುತ್ತಾರೆ. "
        "ಇದು ಲಾಭದಾಯಕವಾಗಿದ್ದು ಸುಲಭವಾಗಿ ನಿರ್ವಹಿಸಬಹುದು. ಹೆಚ್ಚಿನ ಮಾಹಿತಿಗೆ ನಮ್ಮ ಕೋರ್ಸ್‌ಗಳನ್ನು ನೋಡಿ."
    ),
    "Tamil": (
        "இந்தியாவில் சிறிய அளவில் பசு பண்ணை தொடங்க 10 முதல் 15 பசுக்கள் போதுமானவை. "
        "இது மும்பை நடத்தை மற்றும் லாபகரமானது. மேலும் விவரங்களுக்கு எங்கள் பாடங்களைப் பார்க்கவும்."
    ),
    "Telugu": (
        "భారతదేశంలో చిన్నపాటి డెయిరీ ఫార్మ్‌ ప్రారంభించడానికి సాధారణంగా 10 నుండి 15 ఆవులు సరిపోతాయి. "
        "ఇది లాభదాయకంగా ఉండటమే కాకుండా సులభంగా నిర్వహించవచ్చు. మరిన్ని వివరాలకు మా కోర్సులు చూడండి."
    ),
    "Malayalam": (
        "ഇന്ത്യയിൽ ചെറുതായി ഡയറി ഫാം തുടങ്ങാൻ 10 മുതൽ 15 പശുക്കൾ ആരംഭിക്കാൻ പോരും. "
        "ഇത് ലാഭകരവും കൈകാര്യം ചെയ്യാൻ എളുപ്പവുമാണ്. കൂടുതൽ വിവരങ്ങൾക്ക് ഞങ്ങളുടെ കോഴ്സുകൾ നോക്കുക."
    ),
}

def get_dairy_farm_practical_answer(query):
    """
    Returns a practical answer about dairy farm cows in the proper language, if the question matches.
    """
    # Dairy-farm intent triggers (add more as needed)
    triggers = [
        "how many cows", "how many cow", "डेयरी फार्म", "कितनी गाय",
        "ಗಾಯ್ ಎಷ್ಟು", "ಎಷ್ಟು ಗೋವುಗಳು", "എത്ര പശു", "எத்தனை மாடு", "ఎన్ని ఆవులు"
    ]
    if any(t in query.lower() for t in triggers):
        lang = detect_language_name(query)
        return DAIRY_FARM_INFO.get(lang, DAIRY_FARM_INFO["English"])
    return None

# Streamlit chat window history
if "history" not in st.session_state:
    st.session_state["history"] = []

with st.sidebar:
    st.subheader("Demo prompts")
    for prompt in [
        "Tell me about honey bee farming course",
        "I want to learn how to start a poultry farm",
        "Do you have any courses in Tamil?",
        "I am a recent high school graduate, are there any opportunities for me?",
        "डेयरी फार्म शुरू करने के लिए कितनी गाय चाहिए?",
        "Are there any stores near Whitefield, Bangalore where I can buy seeds for papaya farming?"
    ]:
        if st.button(prompt):
            st.session_state["q"] = prompt

q = st.text_input(
    "Ask about courses",
    value=st.session_state.get("q", ""),
    placeholder="e.g., Tell me about honey bee farming course"
)

ask_clicked = st.button("Ask")

if ask_clicked or q:
    query = (q or "").strip()
    if not query:
        st.stop()

    # Practical Dairy Farm response (in 6 lang)
    practical_dairy = get_dairy_farm_practical_answer(query)
    if practical_dairy:
        st.session_state["history"].append({"user": query, "bot": practical_dairy})
        for turn in st.session_state["history"]:
            st.markdown(f"**You:** {turn['user']}")
            if turn["bot"]:
                st.markdown(f"{turn['bot']}\n---")
        st.stop()

    # Bonus 2: Store lookup for papaya seeds near Whitefield
    is_whitefield_query = ("whitefield" in query.lower()) and ("seed" in query.lower() or "store" in query.lower())
    if is_whitefield_query:
        with st.spinner("Looking up nearby stores…"):
            results = find_seed_stores_near_whitefield()
        if not results:
            st.info("No external results right now. Try again later.")
        else:
            st.session_state["history"].append({"user": query, "bot": None})
            st.subheader("Nearby stores for papaya seeds")
            for s in results:
                st.write(f"**{s.get('name','(unknown)')}**")
                if s.get('address'): st.write(s['address'])
                if s.get('rating'): st.write(f"Rating: {s['rating']}")
                st.write("---")
        st.stop()

    # Otherwise, query dataset — answer in chat style!
    lang_filter = query_requests_language_filter(query)
    if lang_filter:
        hits = index.filter_by_language(lang_filter, k=100)
    else:
        hits = index.search(query, k=6)

    if not hits or (not lang_filter and hits[0].score < 0.05):
        detected = detect_language_name(query)
        response = OUT_OF_SCOPE.get(detected, OUT_OF_SCOPE["English"])
    else:
        response = format_courses_response(hits, query, lang_filter=lang_filter)

    st.session_state["history"].append({"user": query, "bot": response})

# Show conversation like a real chat
for turn in st.session_state["history"]:
    st.markdown(f"**You:** {turn['user']}")
    if turn["bot"]:
        st.markdown(f"{turn['bot']}\n---")

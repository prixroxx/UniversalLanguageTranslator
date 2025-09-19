import streamlit as st
from openai import OpenAI
from typing import Dict
import json

# Loading API Key From User. Provide it in the Sidebar.

# configure the page
st.set_page_config(
    page_title="Intelligent Translator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# supported languages with their codes and flags
LANGUAGES = {
    "english": {"code": "en", "flag": "🇬🇧"},
    "spanish": {"code": "es", "flag": "🇪🇸"},
    "french": {"code": "fr", "flag": "🇫🇷"},
    "german": {"code": "de", "flag": "🇩🇪"},
    "italian": {"code": "it", "flag": "🇮🇹"},
    "portuguese": {"code": "pt", "flag": "🇵🇹"},
    "chinese": {"code": "zh", "flag": "🇨🇳"},
    "japanese": {"code": "ja", "flag": "🇯🇵"},
    "korean": {"code": "ko", "flag": "🇰🇷"},
    "russian": {"code": "ru", "flag": "🇷🇺"},
    "arabic": {"code": "ar", "flag": "🇸🇦"},
    "hindi": {"code": "hi", "flag": "🇮🇳"},
    "dutch": {"code": "nl", "flag": "🇳🇱"},
    "swedish": {"code": "sv", "flag": "🇸🇪"},
    "norwegian": {"code": "no", "flag": "🇳🇴"},
}

# initialise session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "translation_history" not in st.session_state:
    st.session_state.translation_history = []
if "target_language" not in st.session_state:
    st.session_state.target_language = "english"

def create_translation_prompt(text: str, target_lang: str) -> str:
    """create a sophisticated system prompt for translation tasks"""
    return f"""You are an expert linguist and cultural translator. Your task is to:

1. DETECT the language of the input text
2. TRANSLATE it to {target_lang}
3. PROVIDE cultural context when relevant

respond in this exact JSON format:
{{
    "detected_language": "language name",
    "confidence": 0.95,
    "primary_translation": "main translation here",
    "alternatives": ["alternative 1", "alternative 2"],
    "cultural_notes": "cultural context or regional variations",
    "formality_level": "formal/informal/neutral",
    "literal_translation": "word-for-word if different from primary"
}}

rules:
- be accurate but culturally aware
- include alternatives only if they're meaningfully different
- add cultural notes for idioms, slang, or regional expressions
- if the text is already in the target language, set detected_language accordingly and explain
- confidence should reflect how certain you are about language detection (0.0-1.0)

text to analyse: "{text}" """

def detect_and_translate(text: str, target_lang: str, api_key: str) -> Dict:
    """detect language and translate with cultural context"""
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={"HTTP-Referer": "localhost:8080"} # Required by OpenRouter for rankings
        )
        
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": create_translation_prompt(text, target_lang)},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        # parse the JSON response
        result = json.loads(response.choices[0].message.content)
        return result
        
    except json.JSONDecodeError:
        return {"error": "failed to parse translation response"}
    except Exception as e:
        return {"error": f"translation failed: {str(e)}"}

def format_translation_response(result: Dict, original_text: str) -> str:
    """format the translation result for display"""
    if "error" in result:
        return f"❌ {result['error']}"
    
    detected = result.get("detected_language", "unknown")
    confidence = result.get("confidence", 0.0)
    translation = result.get("primary_translation", "")
    alternatives = result.get("alternatives", [])
    cultural = result.get("cultural_notes", "")
    formality = result.get("formality_level", "")
    literal = result.get("literal_translation", "")
    
    # get flag for detected language
    detected_flag = ""
    for lang, info in LANGUAGES.items():
        if lang.lower() == detected.lower():
            detected_flag = info["flag"]
            break
    
    response = f"""🔍 **Detected language**: {detected_flag} {detected} (Confidence: {confidence:.1%})

🎯 **Translation**: "{translation}" """
    
    if formality and formality != "neutral":
        response += f"\n📝 **Tone**: {formality}"
    
    if alternatives:
        response += f"\n🌟 **Alternatives**: {', '.join([f'"{alt}"' for alt in alternatives])}"
    
    if literal and literal != translation:
        response += f"\n📖 **Literal**: {literal}"
    
    if cultural:
        response += f"\n💡 **Cultural Context**: {cultural}"
    
    return response

# sidebar configuration
with st.sidebar:
    st.header("⚙️ Translation Settings")
    
    # API key input
    api_key = st.text_input(
        "OpenRouter api key",
        type="password",
        help="enter your openrouter api key to enable translation"
    )
    
    # target language selection
    target_lang_display = st.selectbox(
        "translate to:",
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(st.session_state.target_language),
        format_func=lambda x: f"{LANGUAGES[x]['flag']} {x.title()}"
    )
    refresh_history = st.button("🔄 refresh history", use_container_width=True)
    # update target language and refresh history if changed
    if refresh_history:
        st.session_state.target_language = target_lang_display
        st.balloons()
        st.rerun()
    
    if target_lang_display != st.session_state.target_language:
        st.session_state.target_language = target_lang_display
        st.rerun()
    
    st.markdown("---")
    
    # translation history
    if st.session_state.translation_history:
        st.subheader("📚 recent translations")
        for i, (source, target, src_lang, tgt_lang) in enumerate(
            reversed(st.session_state.translation_history[-5:])
        ):
            with st.expander(f"{src_lang} → {tgt_lang}", expanded=False):
                st.text_area(
                    "original:",
                    value=source,
                    height=60,
                    key=f"hist_src_{i}",
                    disabled=True
                )
                st.text_area(
                    "translation:",
                    value=target,
                    height=60,
                    key=f"hist_tgt_{i}",
                    disabled=True
                )
    
    # clear history button
    if st.button("🗑️ clear history", use_container_width=True):
        st.session_state.translation_history.clear()
        st.rerun()

# main interface
st.title("🌍 Intelligent Translator")
st.caption("Automatic Language Detection • Cultural Context • Alternative Translations")

if not api_key:
    st.warning("⚠️ Please enter your openrouter api key in the sidebar to start translating...")
    st.info("🤖 This translator uses gpt-4o-mini to provide culturally aware translations with context. You can incur costs, be mindful.")
    st.stop()

# display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# chat input
if prompt := st.chat_input("Type anything in ANY language..."):
    # add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # process translation
    with st.chat_message("assistant"):
        with st.spinner("detecting language and translating..."):
            result = detect_and_translate(
                prompt, 
                st.session_state.target_language,
                api_key
            )
            
            if "error" not in result:
                response = format_translation_response(result, prompt)
                
                # add to translation history
                st.session_state.translation_history.append((
                    prompt,
                    result.get("primary_translation", ""),
                    result.get("detected_language", "unknown"),
                    st.session_state.target_language
                ))
            else:
                response = format_translation_response(result, prompt)
            
            st.write(response)
            
            # add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})

# footer with tips
st.markdown("---")
with st.expander("💡 Pro Tips", expanded=False):
    st.markdown("""
    **for best results:**
    - try idioms, slang, or cultural expressions to see cultural context in action
    - the bot works with formal and informal text equally well  
    - it can handle everything from shakespeare to tiktok comments
    - use complete sentences when possible for better context
    
    **examples to try:**
    - "it's raining cats and dogs" 
    - "je suis dans le pétrin"
    - "breaking bad was lit"
    - "お疲れ様でした"
    """)

# styling
st.markdown("""
<style>
.stTextInput > div > div > input {
    background-color: #f0f2f6;
}

.stSelectbox > div > div > select {
    background-color: #f0f2f6;
}

div[data-testid="metric-container"] {
    background-color: #f0f2f6;
    border: 1px solid #ddd;
    padding: 5% 5% 5% 10%;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

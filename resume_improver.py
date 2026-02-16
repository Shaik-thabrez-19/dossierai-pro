import streamlit as st
import time

# Simple page config
st.set_page_config(
    page_title="AI Resume Improver",
    page_icon="📄",
    layout="centered"
)

# Simple HTML/CSS that won't cause issues
st.markdown("""
<style>
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    h1 {
        color: white !important;
        text-align: center;
        font-size: 3rem !important;
        padding: 2rem !important;
    }
    .stText {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1>🤖 AI Resume Improver</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: white;'>Upload your resume and get instant improvement suggestions</p>", unsafe_allow_html=True)

# Simple file upload
uploaded_file = st.file_uploader("Choose a text file", type=['txt'])

def simple_analyze(text):
    suggestions = []
    words = len(text.split())
    
    if words < 100:
        suggestions.append("⚠️ Your resume is too short. Add more content.")
    if "skill" not in text.lower():
        suggestions.append("💡 Add a skills section.")
    if "project" not in text.lower():
        suggestions.append("📁 Include your projects.")
    if "experience" not in text.lower():
        suggestions.append("💼 Add work experience.")
    
    return suggestions, words

if uploaded_file is not None:
    try:
        # Read file
        text = uploaded_file.read().decode('utf-8')
        st.success("✅ File uploaded!")
        
        # Preview
        with st.expander("Preview Resume"):
            st.text(text[:300])
        
        # Analyze button
        if st.button("Analyze Resume"):
            with st.spinner("Analyzing..."):
                time.sleep(1)
                suggestions, word_count = simple_analyze(text)
                
                # Show metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Word Count", word_count)
                with col2:
                    st.metric("Suggestions", len(suggestions))
                
                # Show suggestions
                st.subheader("Improvement Suggestions:")
                for s in suggestions:
                    st.info(s)
                    
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: white;'>Developed by Shaik Daniya Thabrez 🚀</p>", unsafe_allow_html=True)
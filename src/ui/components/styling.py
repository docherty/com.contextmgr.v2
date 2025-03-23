import streamlit as st

def add_custom_css():
    st.markdown("""
    <style>
        /* Work Package styling */
        .stButton button {
            padding: 0.2rem 0.5rem;
        }
        
        /* Make edit buttons more compact */
        div[data-testid="column"] > div[data-testid="stButton"] > button {
            line-height: 1;
            padding: 0rem 0.3rem;
        }
        
        /* Make text inputs less tall */
        div.stTextInput > div > div > input {
            padding: 0.3rem;
        }
    </style>
    """, unsafe_allow_html=True)
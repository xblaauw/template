import streamlit as st
from streamlit import session_state as state

from lib import config

st.set_page_config(**config.DEFAULT_PAGE_CONFIG)


st.title('test')


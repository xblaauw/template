import streamlit as st
import requests


st.title('Course platform')


response = requests.get("http://api:8000/example")
st.write(response.json())












##### REALLY BASIC BUT IT ALLOWS ME TO PLACE A PAYMENT!

# payment_code ='''
# <script async
#   src="https://js.stripe.com/v3/buy-button.js">
# </script>

# <stripe-buy-button
#   buy-button-id="buy_btn_1Qrj8UP8gnTF0LwQmvBS9d7T"
#   publishable-key="pk_test_51QrguXP8gnTF0LwQD0a7bbn3Hv30y6CFeeEx7Jv9dzmHqqAU1EtuVPLjLXb2LA3R0fDJKk7wDfIOGVZ3eSjCkzZP00u1eajzy0"
# >
# </stripe-buy-button>
# '''

# import streamlit.components.v1 as components

# components.html(payment_code, height=370)
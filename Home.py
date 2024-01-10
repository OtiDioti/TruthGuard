from openai import OpenAI
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from st_pages import hide_pages # needed to hide pages
#%% page settings
st.set_page_config(page_title = 'TruthGuard', 
                   layout = 'centered', 
                   page_icon = ':house:',
                   menu_items={
                   'Get Help': 'https://github.com/OtiDioti/TruthGuard/issues',
                   'Report a bug': "https://github.com/OtiDioti/TruthGuard/issues",
                   'About': "**The app is work in progress: any comment/suggestion/request is welcome!**"},
                   initial_sidebar_state="collapsed")

#%% hiding pages from sidebar
st.session_state['pages_to_hide'] = 'ChatGPT'
hide_pages(st.session_state['pages_to_hide'])
#%% 
def IsKeyValid(key):
    """This function will check that the provided OpenAI key is valid"""
    client = OpenAI(api_key = key)
    try:
        response = client.chat.completions.create(
                   model = "gpt-3.5-turbo",
                   messages = [{"role": "user", "content": "hi"}], 
                   max_tokens = 5
                   )
    except:
        return False
    else:
        return True
#%% Title
st.title('Welcome to TruthGuard!')
#%% Text bar that will be used by user to inser OpenAI key
text_input_container = st.empty() # showcase bar
api_key = st.text_input('Insert OpenAi API key (this will be not registered anywhere):') # asking for key

printed = False # has the error message been printed?
while api_key != "" and printed == False: # if the user is inserting an input
    if IsKeyValid(api_key): # if the key is valid
        st.session_state['API_key'] = api_key   
        if IsKeyValid(st.session_state['API_key']):
            switch_page('ChatGPT') # open chat 
            api_key = "" # resetting variable
    else:
        printed = True # the error message has been printed
        st.info('The provided key is invalid') # ask for valid key
#%% Info text
st.write("""🕵️‍♂️ Welcome to FactCheckAI – Empowering You Against Fake News! 🤖🔍

Before you dive into the vast ocean of information, let's shed light on what FactCheckAI is all about.

🎯 Mission:
Our primary mission is to assist you in fact-checking information sourced from the internet or encountered in daily conversations. While achieving objective fact-checking for every piece of information remains a formidable challenge, we've tailored our focus to recent events covered by news outlets. This ensures a more efficient and relevant verification process.

🌐 Purpose:
Born out of a passion for honing programming skills, FactCheckAI is more than just a project – it's a tool designed to enhance your ability to discern credible information. However, please note that the results obtained through this platform are best approached with a discerning eye and taken lightly.

💡 Optimal Performance Tips:
For the best results, we recommend providing concise and direct information when prompted. This helps FactCheckAI deliver swift and accurate assessments, empowering you with the knowledge needed to navigate today's information-rich landscape.

🤖 GPT-4 Power:
FactCheckAI is powered by the cutting-edge GPT-4, a state-of-the-art language model. Harnessing the capabilities of this advanced AI technology, we aim to elevate your fact-checking experience to new heights.

🔒 Your Information Guardian:
Rest assured, FactCheckAI is here to be your vigilant information guardian, tirelessly working to sift through the noise and provide you with credible insights.

🌟 Why FactCheckAI?

    Swift and efficient fact-checking.
    Tailored focus on recent events from news outlets.
    Powered by GPT-4 for advanced language understanding.
    Developed with a passion for programming and a commitment to your information well-being.

Ready to navigate the information landscape with confidence? Let FactCheckAI be your guide! 🚀🔗""")




    
    

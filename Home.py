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
st.write('## Wait!!! Before continuing it can be important and useful to understand what this project is about')
st.write("""The aim of this project is to help with the fact checking of information found on the internet or overheard in conversations.
         However, note that an objective fact checking of any piece of information is a quasi-impossible task to achieve.
         The way we handle this is by optimizing for the fact checking of recent events that made it to news outlet. More importantly, this 
         project was born from my need to implement software programs to practice my programming abilities, and therefore any of the results obtained 
         via this project should be taken lightly. 
         \n For optimal performance we suggest keeping the prompted facts as concise and as direct as possible. Also, despite the intented purpose of this program
         try to avoid making use of data within the prompt line (i.e. instead of prompting "Marco has 5 apples" try with "How many apples does marco have?") """)





    
    

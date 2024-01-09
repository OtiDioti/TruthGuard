from openai import OpenAI
import streamlit as st
import os 
import sys
dir_path = os.path.dirname(os.path.realpath(__file__)) # current directory
prev_dir = os.path.abspath(os.path.join(dir_path, os.pardir)) # parent of current directory
sys.path.append(prev_dir+'/Modules')
from st_pages import hide_pages # needed to hide pages
import time
from GoogleSearchingAndFiltering import GoogleSearcher, DuplicateLinkEraser, ArticleExtracter, VectorSearchFilter, NumTokensFromString
from QueriesGenerator import QueryGenerator
#%% Useful Function (readibility)
def UsefulSplits(prompt, nr_of_searches = 4, 
                 period = "7d", results_per_google_page = 2, sleep_time = 4,
                 splits_to_include_per_article = 3, max_tokens = 8e3):
    """This function will take in the information to be fact checked and will return 
    a list of chunk of text that gpt will use to fact check the piece of information to be fact
    checked."""
    queries = QueryGenerator(client, prompt, nr_of_searches) # generating the queries to perform google searches
    urls = [] # empty list of urls
    for query in queries: # iterating over all queries
        urls += GoogleSearcher(query, period)[:results_per_google_page] # only obtaining the first 4 results from the last 7 days
        time.sleep(sleep_time) # waiting sleep_time seconds between each search to avoid getting problems with google api
    urls = DuplicateLinkEraser(urls) # eliminating duplicate results
    articles = [] # empty list of articles corresponding to each url
    for url in urls: # iterating over all urls
        tmp = url[url.find("https://") + 8:] # obtaining main journal url
        tmp = tmp[:tmp.find("/")] # obtainining main journal url
        articles.append({"journal" : tmp, 
                         "article" : ArticleExtracter(url)}) # extracting main body of article and appending it as a dict
    splits_list = [] # empty list of all splits with their relevancy score
    for tmp in articles:
        sorted_data = sorted(VectorSearchFilter(prompt, tmp["article"], openai_key), key = lambda x: x[1]) # sorting in increasing order according to scores    
        sorted_splits = [item[0] for item in sorted_data] # this contains all ordered splits
        splits_list.append((tmp["journal"], sorted_splits[:splits_to_include_per_article])) # appending ordered splits with corresponding origin url
    
        
    while sum([NumTokensFromString(" ".join(splits[1])) for splits in splits_list]) > max_tokens: # while the useful splits are too many to be all fed to gpt
        splits_list = []
        splits_to_include_per_article -= 1
        if splits_to_include_per_article == 0: # if we are not including any more splits
            break
        for tmp in articles:
            splits_list.append((tmp["journal"], sorted_splits[:splits_to_include_per_article])) # appending ordered splits with corresponding origin url
    return splits_list

def Beautifier(tuples_list):
    """This function takes in a list of tuples and returns a single string where
    each separate strting has been separated as needed"""
    tmp = ""
    for item in tuples_list:
        tmpp = " ".join(item[1])
        tmp += f"Article extracts from {item[0]}: {tmpp}.  "
    return tmp
#%% setting up page and set of variables
hide_pages(st.session_state['pages_to_hide']) # hiding pages from sidebar
openai_key = st.session_state['API_key'] # extracting api key
#### setting up key and getting access to OpenAI API ####
client = OpenAI(api_key = openai_key)
#%% Setting up the initial state of the language model
sys_prompt = """You are to receive a piece of text in the form of a question or statement 
 to be fact checked. To do this you will also be provided with extracts of articles previously
 obtained by performing google searches. Use these pieces of articles to infer the veridicity (or answer) of the
 first piece of text provided. Try to be exahustive when explaining your reasoning. If no useful information was
 provided then state so, by suggesting to rephrase the initial statement/question. If contrasting information is provided
 make a note of this. When answering, make sure to quote all the article extracts used to determine the final verdict
 and include from where these extracts where obtained. Lastly ignore all empty article extracts you may receive."""

gpt_answer = """Ok."""

st.session_state.messages = [
    {'role':'system', 'content':sys_prompt.replace("\n", "")},
    {'role':'assistant', 'content':gpt_answer.replace("\n", "")},
]

#%%
st.title("TruthGuard (beta)") # adds title to page


for message in st.session_state.messages[3:]: # iterating through the messages avoiding the set up
    with st.chat_message(message["role"]): # st.chat_message(user = 'role') this will show who is writing
        st.markdown(message["content"]) # this will show the content of the message

topic_counter = 0 # this will count at which topic the discussion has arrived
if prompt := st.chat_input("What is the piece of information you would like to fact check?"): # within the chat bar
   useful_info = UsefulSplits(prompt) # list of tuples containing the strings containing useful info to fact check prompt and the main url from where these were taken from
   useful_info = Beautifier(useful_info) # obtaining a single string from list
   usr_nudge = f"""The piece of text to be fact checked is {prompt}. To fact check this
    use the following article extracts {useful_info}""" # this will be used to tell gpt where to look for answers
    
   st.session_state.messages.append({"role": "user", "content": usr_nudge}) # appending prompt of user to message history
   with st.chat_message("user"): # will show that the prompt has been composed by user
        st.markdown(prompt) # will show the prompt input by the user
    
   with st.chat_message("assistant"): # showing that it is the assistant speaking
        message_placeholder = st.empty() 
        full_response = "" # initializing response string
        response = client.chat.completions.create(
                   model = "gpt-4",
                   messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                   )
        full_response += response.choices[0].message.content
        message_placeholder.markdown(full_response)
   st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    
    

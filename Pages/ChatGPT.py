from openai import OpenAI
from pynytimes import NYTAPI
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
def UsefulSplits(prompt, nr_of_searches = 3, 
                 period = "7d", results_per_google_page = 4, sleep_time = 3,
                 splits_to_include = 15, max_tokens = 8e3):
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
        articles.append(ArticleExtracter(url)) # extracting main body of article and appending it 
    splits_list = [] # empty list of all splits with their relevancy score
    for article in articles:
        article_splits = VectorSearchFilter(prompt, article, openai_key) # obtaining the filtering and list of tuples of splits and relative relevancy score
        splits_list += article_splits
    sorted_data = sorted(splits_list, key = lambda x: x[1]) # sorting in increasing order according to distances    
    sorted_splits = [item[0] for item in sorted_data] # this contains all splits in order of increasing distance
    useful_splits = sorted_splits[:splits_to_include] # taking the first 5 splits as the only ones that gpt will have to read
    while sum([NumTokensFromString(splits) for splits in useful_splits]) > max_tokens: # while the useful splits are too many to be all fed to gpt
        useful_splits.pop(-1) # remove the least relevant split
    return useful_splits

def Beautifier(string_list):
    """This function takes in a list of strings and returns a single string where
    each separate strting has been separated as needed"""
    tmp = ""
    for idx, string in enumerate(string_list):
        tmp += f"Article Extract nr. {idx + 1}: {string}.  "
    return tmp
#%% setting up page and set of variables
hide_pages(st.session_state['pages_to_hide']) # hiding pages from sidebar
openai_key = st.session_state['API_key'] # extracting api key
language = st.session_state['selected_language'] #  what language deos the user want to practice?
news_section = st.session_state['top_story_section'] #  what section of the top stories on the nyt should be scanned
#### setting up key and getting access to OpenAI API ####
client = OpenAI(api_key = openai_key)
nyt_key = open(prev_dir + '/Modules/nytkey.txt', 'r').read().strip() # obtains nyt API key from the current directory
nyt = NYTAPI(nyt_key, parse_dates = True) # connecting to NYT servers using the key

#%% Setting up the initial state of the language model
sys_prompt = """You are to receive a piece of text in the form of a question or statement 
 to be fact checked. To do this you will also be provided with extracts of articles previously
 obtained by performing google searches. Use these pieces of articles to infer the veridicity of the
first piece of text provided. Try to be exahustive when explaining your reasoning. If no useful information was
provided then state so, by suggesting to rephrase the initial statement/question. If contrasting information is provided
make a note of this."""

gpt_answer = """Ok."""

st.session_state.messages = [
    {'role':'system', 'content':sys_prompt.replace("\n", "")},
    {'role':'assistant', 'content':gpt_answer.replace("\n", "")},
]

#%%
st.title("TrendLingo (beta)") # adds title to page


for message in st.session_state.messages[3:]: # iterating through the messages avoiding the set up
    with st.chat_message(message["role"]): # st.chat_message(user = 'role') this will show who is writing
        st.markdown(message["content"]) # this will show the content of the message

topic_counter = 0 # this will count at which topic the discussion has arrived
if prompt := st.chat_input("What is the piece of information you would like to fact check?"): # within the chat bar
   useful_info = UsefulSplits(prompt) # list of strings containing useful info to fact check prompt
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
                   model = st.session_state["openai_model"],
                   messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                   )
        full_response += response.choices[0].message.content
        message_placeholder.markdown(full_response)
   st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    
    

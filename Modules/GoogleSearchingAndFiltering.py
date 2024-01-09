import os 
from GoogleNews import GoogleNews
from newspaper import Article
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
import tiktoken # needed to estimate the number of tokens
from scipy.spatial import distance # will be used to obtain cosine distance
#%%
def ArticleExtracter(url):
    """Given a url this function returns the main body of text contained within it"""
    article = Article(url) # extracting article
    article.download() # downloading article
    article.parse() # parsing the article
    main_body = article.text.strip().replace("\n", "") # obtaining article's main text (this will often return only 1 paragraph, as most nyt articles are locked behind paywall)
    return main_body

def DuplicateLinkEraser(urls_list):
    """takes in a list of urls and returns a new list of urls where all duplicates
    have been removed"""
    return list(dict.fromkeys(urls_list)) # converting to dictionary will automatically remove all duplicate indices

def GoogleSearcher(query, lang = 'en', region = None, period = '7d'):
    """Given a search query, this function will return a list of urls
    for the first page of results obtained by googling in the google news section.
    """
    googlenews = GoogleNews(lang = lang, region = region, period = period) # initializing with english language with no focus on which region, last 7 days
    googlenews.enableException(True) # enable to throw exeptions
    googlenews.search(query) # obtain news about "query"
    page_1_results = googlenews.page_at(1) # extract list of dictionaries for page 1
    urls = [page_1_results[i]['link'] for i in range(len(page_1_results))] # obtaining the urls found during the search
    return urls

def GroupSummarizer(texts_list, client, model = 'gpt-4', max_tokens = 8e3):
    """This function takes in a list of strings, summarizes each one of them and 
    then constructs a summary of all the summaries"""
    prompt = """You will now be provided with a piece of text extracted from a larger article.
    Your task is to provide a short summary of this which must contain less characters
    than the original. It is imperative you only provide a summary and nothing else.""" # gpt answer to prompt
    answr = """Ok. I will read the provided text and I will answer with only a shorter
    summary of this piece of text.""" # gpt answer to prompt
    summaries = [] # initializing list of summaries
    tmp = "" # needed to check that summaries are short enough
    for text in texts_list: # iterating over the list of texts
        qstn = f"""The text to be summarized reads: {text}""" # specifying which text needs to be summarized 
        response = client.chat.completions.create(
                   model = model,
                   messages = [{"role":"system", "content":prompt.replace("\n", "")},
                               {"role":"assistant", "content":answr.replace("\n", "")},
                               {"role":"user", "content":qstn.replace("\n", "")}]
                   ) # obtaining response    
        full_response = response.choices[0].message.content.replace("\n", "").replace("\\", "")  # extracting response text
        summaries.append(full_response) # appending summary
        tmp += full_response + " --- " # adding response with a arbitrary divider
    counter = 0 # initializing a counter that will break the following while loop in case of danger    
    while NumTokensFromString(tmp) >= max_tokens: # in case the collection of all summaries is too large to be fed to gpt-4
        if counter >= 5: # if we looped 5 or more times already
            print("Error with creating summarries that are short enough to be fed to GPT.")
            break # stop!
        else:
            tmp = "" # needed to check that summaries are short enough
            for text in summaries: # iterating over summaries to make them even shorter
                summaries.pop(0) # removing the current "text" from the list of summaries
                qstn = f"""The text to be summarized reads: {text}""" # specifying which text needs to be summarized 
                response = client.chat.completions.create(
                           model = model,
                           messages = [{"role":"system", "content":prompt.replace("\n", "")},
                                       {"role":"assistant", "content":answr.replace("\n", "")},
                                       {"role":"user", "content":qstn.replace("\n", "")}]
                           ) # obtaining response    
                full_response = response.choices[0].message.content.replace("\n", "").replace("\\", "")  # extracting response text
                summaries.append(full_response) # appending summary of the summary
                tmp += full_response +" --- "   
            counter += 1 # adding 1 to counter
    #### summarizing the summaries into a single summary ####
    prompt = """You will now be provided with a series of pieces of text separated
    by triple dashes (e.g. text1 --- text2 --- ...). Your task is to read them 
    and create a summary summarizing the concepts contained in all of the pieces 
    of text. It is imperative you only provide a summary and nothing else.""" # gpt answer to prompt
    answr = """Ok. I will read the provided texts and I will answer with only a shorter
    summary of these pieces of text.""" # gpt answer to prompt
    qstn = f"""The pieces of text to be summarized read: {tmp}""" # this will prompt gpt4 to generate a prompt
    response = client.chat.completions.create(
               model = model,
               messages = [{"role":"system", "content":prompt.replace("\n", "")},
                           {"role":"assistant", "content":answr.replace("\n", "")},
                           {"role":"user", "content":qstn.replace("\n", "")}]
               ) # obtaining response    
    full_response = response.choices[0].message.content.replace("\n", "").replace("\\", "")  # extracting response text
    return full_response

def NumTokensFromString(string, model = "cl100k_base"):
    """Given a string this function will separate it into tokens and return the
    number of tokens contained in a string"""
    encoding = tiktoken.get_encoding(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def VectorSearchFilter(test_sample, sample_to_be_filtered, key,
                       model = "gpt-4", chunk_size = 1200, chunk_overlap = 300,
                       max_tokens = 8e3):
    """This function takes in a piece of text (sample_to_be_filtered) and compares
    it with a 'test_sample'. It then returns whether or not the piece of text contain
    information relevant to the test_sample. This is done by taking the sample_to_be_filtered
    and separating it into chunks of a certain size with a certain overlap between chunks.
    The chunks are then embedded into vectors and the same is done with the test_sample 
    (hopefully the test sample is small enough to be embedded without having to split it). 
    The function then returns the text chuncks with associated relevancy score."""
    #### setting up OpenAI key ####
    
    os.environ["OPENAI_API_KEY"] = key
    
    #### splitting text into chunks with some overlap between them ####
    
    n_test_tokens = NumTokensFromString(test_sample) # nr of tokens used by the test_sample
   
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size, chunk_overlap = chunk_overlap, add_start_index=True) # we’ll split our documents into chunks
    sample_splits = text_splitter.split_text(sample_to_be_filtered) # this is now a list of stings with the specifized chunk_size 
    vectorstore = OpenAIEmbeddings().embed_documents(sample_splits) # this returns a list of lists where each sub list is the vector embedded version of one of the splits
    
    if n_test_tokens >= max_tokens: # if test_sample would require more than 8k tokens
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size, chunk_overlap = chunk_overlap, add_start_index=True) # we’ll split our documents into chunks
        test_splits = text_splitter.split_text(test_sample) # this is now a list of stings with the specifized chunk_size 
        summary = GroupSummarizer(test_splits) # reduce dimensionality of test_sample
        test_vector = OpenAIEmbeddings().embed_query(summary) # this returns a list of lists where each sub list is the vector embedded version of one of the splits
    else:
        test_vector = OpenAIEmbeddings().embed_query(test_sample) # vectorize the full thing
    distances = [] # initializing list of distances
    for vector_sample in vectorstore: # iterating over all vectors within vectorstore
        distances.append(distance.cosine(vector_sample, test_vector)) # appending the cosine distance between the sample_vector and the test_vector
    combined_data = list(zip(sample_splits, distances)) # combining distances with corresponding splits
    return combined_data # avrg will be used to determine the releveance of a given article, while the splits will be used to obtain summaries later on (avoid double calculations)

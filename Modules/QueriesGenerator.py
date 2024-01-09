def QueryGenerator(client, piece_of_text = "", n_queries = 2, model = 'gpt-4'):
    """Given a piece of text, this function will return
    n_queries queries to be fed to google to obtain more information regarding the
    topic covered within the piece of text."""
    prompt = f"""You will now receive a piece of text, in the form of a question or a statement, that the user wishes to fact check.
    Your task is to generate {n_queries} queries to be used to perform {n_queries} separate google searches
    aimed at fact checking the piece of information previously mentioned. It is imperative that you provide only the 
    queries (i.e. no introductiory text or anything else that is not a query) and that you write 
    each query on a single line and separate them by introducing three dashes (i.e. '---') as such: 
    'query1 --- query2...'.""" # system prompt to be fed to gpt
    answr = f"""Ok. Once provided with this piece of text I will generate {n_queries}
    that, if used in a google search, will be guaranteed to return articles containing relevant
    information to fact check the provided piece of text. I will also strictly follow the request of separating 
    each query via the introduction of three dashes (i.e. '---'). Lastly, I will make sure to include only queries
    in my future answers and nothing else.""" # gpt answer to prompt
    qstn = f"""The piece of text in question is {piece_of_text}""" # this will prompt gpt to generate google queries
    response = client.chat.completions.create(
               model = model,
               messages = [{"role":"system", "content":prompt.replace("\n", "")},
                           {"role":"assistant", "content":answr.replace("\n", "")},
                           {"role":"user", "content":qstn.replace("\n", "")}]
               ) # obtaining response
    full_response = response.choices[0].message.content  # extracting response text
    tmp = 0 # this counter will act as a safety net which will break the loop in case gpt cannot return what I need
    while n_queries != full_response.count('---') + 1: # if gpt did not generate the requested amount of queries, or it has not separated them correctly
        tmp += 1
        if tmp >= 5: # if we tried 5 or more times (this is arbitrary)
            break # break the loop
        else:
            response = client.chat.completions.create(
                       model = model,
                       messages = [{"role":"system", "content":prompt.replace("\n", "") },
                                   {"role":"assistant", "content":answr.replace("\n", "") },
                                   {"role":"user", "content":qstn.replace("\n", "") }]
                       ) # obtaining response
            full_response = response.choices[0].message.content # extracting response text
    queries = [] # initializing empty list
    tmp = 0 # initializing an index
    for i in range(n_queries): # iterating through the number of queries
        tmp = full_response.find("---") # finds index of the first instance of "---"
        if tmp == -1: # if it found nothing
            queries.append(full_response.replace("\"","").strip())
            break 
        else:
            queries.append(full_response[:tmp].replace("\"","").strip()) # appending the i-th query
            full_response = full_response[tmp + 3:] # eliminating the i-th query from the full response since this has been appended already      
    return queries # returns list of queries
import os
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from datetime import date

load_dotenv()


def llm_connect(model_name="gpt-3.5-turbo", temperature='0'):
    llm = ChatOpenAI(
        temperature=temperature, model_name=model_name, api_key=os.getenv("OPENAI_API_KEY")
    )
    return llm


def generate_url_prompt(user_query, today_date):
    template: str = """
    Your task is to generate a URL for NewsAPI that directly corresponds to {user_query}. 
    Focus on identifying the most relevant keywords or phrases from the query "{user_query}" to ensure the URL will fetch articles closely related to the topic.

    Key considerations for constructing the URL:
    - Extract the main topic or keywords from "{user_query}" accurately.
    - If there is a date or time frame mentioned, determine the appropriate time frame for the search. If so, today's date is {today_date}. Otherwise, be sure to leave the fields empty.
    - Use the correct language setting based on the query's language.
    - For queries without a date, use general searches and format the URL as follows:
        https://newsapi.org/v2/everything?q={{main-topic-or-keyword}}&pageSize=10
    - For queries with a given date or date range, use specific searches and format the URL as follows:
        https://newsapi.org/v2/top-headlines?q={{main-topic-or-keyword}}&from={{start-date}}&to={{end-date}}&category={{category}}&pageSize=10

    This are the possible categories you can use, if you are not sure for specific queries, pick general as the default category:
    business - entertainment - general - health - science - sports - technology

    Search Example (Specific Search):
    Given the query "NVIDIA Stock Jump this week", construct a URL that fetches the most recent and relevant articles about this topic from NewsAPI. Imagine today's date is 2024-02-29.
    Query output -> https://newsapi.org/v2/top-headlines?q={{US Economy and Stock Market}}&from={{2024-02-23}}&to={{2024-02-29}}&category={{business}}&pageSize=10

    Search Example (General Search):
    Given the query "I want to learn about the climate change" construct a URL that fetches the most recent and relevant articles about this topic from NewsAPI.
    Query output -> https://newsapi.org/v2/everything?q={{Climate Change}}&pageSize=10

    Remember, focus on accuracy and relevancy in your response. Remember, only return the URL generated, don't give any further explanation.
    Also remember, the placeholders within {{}} should be replaced with information relevant to the search query. Aim for precision in keyword selection to ensure the resulting articles are on-topic.
"""
    # Correctly use the named placeholder in the format call
    prompt_template = PromptTemplate(
        template=template, input_variables=["user_query", "today_date"]
    )

    return prompt_template


def generate_search_url(user_query):
    today_date = date.today()
    # Creating an LLMChain instance
    chain = LLMChain(
        llm=llm_connect(), prompt=generate_url_prompt(user_query, today_date)
    )
    # Run the chain to get the response
    response = chain.invoke(input={"user_query": user_query, "today_date": today_date})
    return response["text"]


if __name__ == "__main__":
    query = "NVIDIA Stock Market Jump this week"
    link = generate_search_url(query)

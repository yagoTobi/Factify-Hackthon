import os 
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from query_constructor import llm_connect
from news_extractor import obtain_articles_from_query
import concurrent.futures


load_dotenv()

def extract_facts_prompt(user_query, article):
    template: str = """
        Objective: Extract relevant, unbiased, and factual bullet points from a news article related to the user's search query: {user_query}. 
        Include significant quotes if relevant.

        Instructions to deconstruct the article into bullet points: 

        1. Read and Analyze the Article:
            * Skim through the article to get an overall understanding of its content and main message.
            * Identify the who, what, when, where, and why (5Ws) to grasp the essential facts.
        2. Deconstruct the Article:
            * Introduction: Identify the article's main thesis or argument presented in the introduction.
            * Body: Break down the body into sections or themes. For each section, note the key points, supporting evidence, and factual data.
            * Conclusion: Summarize the conclusion or the final thoughts provided by the author, focusing on the resolution or call to action.
        3. Select Relevant Information:
            *Choose information that directly relates to the user's search query. Focus on facts, findings, data points and relevant statistics.
            *If data metrics are mentioned in the article be sure to include them as a bullet point, along with their explanation. 
            *Avoid subjective opinions or biased language unless it's a direct quote that adds value to the factual reporting.
        4. Extract Bullet Points:
            * Create bullet points that succinctly summarize the key facts and findings. Each bullet point should stand alone in conveying a complete piece of information.
            * If a direct quote is particularly relevant, include it as one of the bullet points, clearly indicating it's a quote with quotation marks and attributing it to the speaker. Furthermore, define if possible who the speaker is.
        5. Maintain Unbiased Reporting:
            * Ensure that each bullet point is presented in a neutral tone, avoiding any language that suggests opinion or bias.
            * Focus on reporting what is known and verified, distinguishing between facts and assertions made within the article.
        6. Review and Refine:
            * Review the bullet points to ensure they are clear, factual, and unbiased. Each point should be directly relevant to the user's search query.
            * Refine the language for clarity and conciseness, ensuring that the bullet points are easily understandable.
        
        Remember the objective of extracting relevant bullet points using the instructions above.
        These bullet points should be created in such a way that you can reconstruct the story in later prompts. 
        Be sure to only reply with the extracted bullet points and quotes.
        ---
        News article to analyse: {article}
    """

    prompt_template = PromptTemplate(
        template=template, input_variables=["user_query", "article"]
    )

    return prompt_template

def extract_facts_articles(user_query, article):
    chain = LLMChain(
        llm = llm_connect(), prompt = extract_facts_prompt(user_query, article)
    )
    response = chain.invoke(input={'user_query':user_query, 'article':article})
    return response['text']

def extract_facts_articles_parallel(user_query, article):
    # Assuming extract_facts_articles is I/O bound, it's suitable for ThreadPoolExecutor
    source_name = article['source']['name']
    source_url = article['url']
    bullet_points = extract_facts_articles(user_query, article['text'])
    return source_name, source_url, article['title'], bullet_points

def article_bullet_points_parallel(user_query, articles_dict):
    bullet_point_articles = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Prepare futures for each article extraction
        futures = [executor.submit(extract_facts_articles_parallel, user_query, article) for article in articles_dict]
        for future in concurrent.futures.as_completed(futures):
            try:
                #TODO - SOURCE URL CHANGE
                #TODO - UP THE TEMPERATURE TO 0.2
                source_name, source_url, title, bullet_points = future.result()
                if source_name not in bullet_point_articles: 
                    bullet_point_articles[source_name] = {
                        'articles': []
                    }
                
                bullet_point_articles[source_name]['articles'].append({
                    'article_url': source_url,
                    'title': title, 
                    'bullet_points': bullet_points
                })
            except Exception as e:
                print(f"An error occurred: {e}")

    return bullet_point_articles

def create_stories_prompt(user_query, bullet_point_articles): 
    template: str = """
    Objective: 
    Act like you are a clear, and expert article journalist in the topics relating to the following query: {user_query}.
    Your job is to synthesize bullet points from multiple articles into a single, cohesive article. 
    The tone should be professional, objective, and unbiased, emulating the writing style of The Economist. 
    After relevant statements considered quotable, insert an HTML reference link with the title of the source, linked to its URL.

    Input Format:
    A dictionary containing series of bullet points for each article, along with corresponding URLs and source names, with the following structures: 
    * Source Name
        * Articles
        * Article URL
        * Title
        * Bullet Points

    Instructions:
        1. Interpret the Dictionary: 
            * For each source in the dictionary, extract the bullet points, article URL, and source name.
            * Note the title for context but primarily focus on the bullet points for content creation. 
        2. Organize Content/Bullet Points:
            * Group bullet points by thematic relevance across all sources, considering the overarching narrative or theme you aim to construct.
            * Arrange these themes logically to ensure a smooth flow from one section to the next in your article.
        3. Create a Professional Tone:
            * Use formal language and an objective tone throughout the article, emulating the style of The Economist.
            * Start with an engaging introduction that summarizes the overarching theme derived from the bullet points.
        3.Structure the Article:
            * Introduction: Briefly introduce the topic(s), highlighting its relevance and the key themes to be discussed.
            * Body: Divide the body into sections based on themes or topics. Each section should start with a clear topic sentence, followed by elaboration and explanation of bullet points, ensuring a logical flow of ideas.
                * Paraphrase or use direct quotes as necessary. 
                
                * Immediately follow the statement with an Markdown reference link formatted as [**_Source Name_**](ARTICLE_URL). Replace ARTICLE_URL with the actual URL and Source Name with the name of the source.
            * Conclusion: Summarize the main points discussed and provide a concluding remark that reflects on the implications or significance of the information presented.
        4. Incorporate Quotes and References:
            * When a statement from the bullet points is directly quoted or is considered significant, include a Markdown reference link after the statement. Format the link as [**_Source Name_**](ARTICLE_URL), where SOURCE_URL is the URL of the source and Source Name is the name of the source.
            * Ensure that each reference link is correctly formatted and accurately reflects the source of the information.
        5. Maintain Objectivity and Unbiased Reporting:
            * Present information and analyses without bias, focusing on facts and supported conclusions.
            * Avoid speculative language or personal opinions, ensuring that the article reflects high journalistic standards.
        6. Review and Edit:
            * Carefully review the draft for coherence, flow, and adherence to the objective and professional tone.
            * Check for grammatical errors and ensure that the Markdown reference links are correctly formatted and functional.
    ----

    Input Dictionary: {bullet_point_dictionary}
    """

    prompt_template = PromptTemplate(
        template=template, input_variables=["user_query", "bullet_point_dictionary"]
    )

    return prompt_template

def generate_article(user_query, bullet_point_dictionary): 
    chain = LLMChain(
        llm=llm_connect(model_name='gpt-4-turbo-preview', temperature=0.23), prompt=create_stories_prompt(user_query, bullet_point_dictionary)
    )
    response = chain.invoke(input={"user_query": user_query, "bullet_point_dictionary": bullet_point_dictionary})
    return response["text"]


def generate_final_article(user_query):
    #user_query = 'Climate Change'
    articles_dict = obtain_articles_from_query(user_query)
    bullet_point_dict = article_bullet_points_parallel(user_query, articles_dict)
    final_article = generate_article(user_query, bullet_point_dict)
    #print(final_article)
    return final_article

def generate_article_from_articles(user_query, articles_dict):
    bullet_point_dict = article_bullet_points_parallel(user_query, articles_dict)
    final_article = generate_article(user_query, bullet_point_dict)
    #print(final_article)
    return final_article

if __name__ == '__main__':
    user_query = 'Climate Change'
    articles_dict = obtain_articles_from_query(user_query)
    bullet_point_dict = article_bullet_points_parallel(user_query, articles_dict)
    final_article = generate_article(user_query, bullet_point_dict)
    print(final_article)

#TODO - LOGO + UI + END-END DEMO + PRESENTACIÓN + PROMPTS + (+1,-1)
#TODO - ElevenLabs
#TODO - PRESENTACIÓN: 
# * Questions Part:
# *     How you could potentially monetise what we’re doing 
# *     B2C Positioning? 
# *     Ads? 
# *     Monetise the podcast -> Free to interact to the agent, by inserting some ads, within the actual loop. 
# *     Channel 1 - NewsAI - You are the driving force for this - Personalised global news network. 
# *     Policy + News - Social Impact 
# * ——
# *     What’s the problem (Stats, the problem, the problem, the problem) -> Future-proofing the news. 
# *     The architecture of the problem -> Maisa 
# *     More technical oriented -> Tell them the story and the vision. 
# *     Don’t mention monetisation 
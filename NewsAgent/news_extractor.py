import os
import ast
import requests
import pandas as pd
import concurrent.futures
from newspaper import Article
from dotenv import load_dotenv
from query_constructor import generate_search_url

load_dotenv()


def get_articles(query):
    # TODO - Uncomment for real demo, right now, we want to save on API usage
    search_url = generate_search_url(query)
    complete_url = search_url + f"&apiKey={os.getenv('NEWSAPI_KEY')}"
    #complete_url = "https://newsapi.org/v2/everything?q=US economy&from=2024-02-23&to=2024-02-29&sortBy=popularity&language=en&pageSize=10&apiKey=6ddc83d9e2974d0fabbac57924805fa3"
    print(complete_url)

    response = requests.get(complete_url)
    if response.status_code == 200:
        articles_json = response.json()
        # * for article in articles_json["articles"]:
        # * print(f"Title: {article['title']}")
        # * print(f"Author: {article['author']}")
        # * print(f"Published At: {article['publishedAt']}")
        # * print(f"Source: {article['source']['name']}")
        # * print(f"URL: {article['url']}\n\n")
        return articles_json["articles"]
    else:
        return None


def extract_article_data(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        return {"text": article.text, "top_image": article.top_image}
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None


def get_maisa_summarize(article):

    url = "https://api.maisa.ai/v1/capabilities/summarize"

    payload = {
        "format": "paragraph",
        "length": "short",
        "text": article
    }
    headers = {
        "X-API-Key": str(os.getenv('MAISA_API_KEY')),
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    summarize = response.text

    summary_dict = ast.literal_eval(summarize)
    summary = summary_dict[list(summary_dict.keys())[0]]

    return summary

def process_articles_concurrently(articles_dict):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Create a future for each article URL
        future_to_article = {
            executor.submit(extract_article_data, article["url"]): article
            for article in articles_dict
        }

        for future in concurrent.futures.as_completed(future_to_article):
            article = future_to_article[future]
            try:
                data = future.result()
                if data:
                    article["text"] = data["text"]
                    article["top_image"] = data["top_image"]
                    article["summary"] = get_maisa_summarize(article["text"])
            except Exception as exc:
                print(f"Article at {article['url']} generated an exception: {exc}")


def dictionary_to_csv(articles_dict):
    folder_path = "./searches"
    # Specify the CSV file name
    csv_file_name = "search_data.csv"
    full_path = os.path.join(folder_path, csv_file_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # Save the DataFrame to a CSV file
    articles_df = pd.DataFrame(articles_dict)
    articles_df.to_csv(full_path, index=False, encoding="utf-8-sig")


def obtain_articles_from_query(query):
    articles_dict = get_articles(query)
    process_articles_concurrently(articles_dict)
    #dictionary_to_csv(articles_dict)
    return articles_dict


# * Cuidado con las fechas manito
# * Llamada a WikiPedia para cosas generales
# * Language specific functions
# TODO - Barrita de busqueda
if __name__ == "__main__":
    articles_dict = obtain_articles_from_query("European Business Updates Last Week")

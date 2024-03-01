import streamlit as st
import time
from news_extractor import obtain_articles_from_query
from article_creator import generate_article_from_articles

st.set_page_config(layout="wide")
# Title or introduction to your app
st.title("Factify")

# Search bar
user_query = st.text_input("Search for stories...", "")

if user_query:
    # Simulating API call delays
    with st.spinner('Fetching articles...'):
        time.sleep(2)  # Adding delay to simulate fetching articles
        article_thumbnails = obtain_articles_from_query(user_query)
        
    left_column, right_column = st.columns([3, 2])  # 60% - 40% width distribution

    # Assuming article_thumbnails is a list of dictionaries with 'title', 'image', 'summary', 'link'
    if article_thumbnails:
        # Generate article content in the left column
        with left_column:
            with st.spinner('Generating article from sources...'):
                time.sleep(5)  # Adding delay to simulate generating article content
                article_content = generate_article_from_articles(user_query, article_thumbnails)
                st.markdown(article_content)
                
        # Display article cards in the right column
        with right_column:
            st.write("Sources Found")
            for index, article in enumerate(article_thumbnails):
                with st.expander(f"{article['title']}"):
                    st.image(article['top_image'], caption=article['title'])
                    st.write(article['summary'])
                    link = f"[Read More]({article['url']})"
                    st.markdown(link, unsafe_allow_html=True)
                    
        # It seems there might be a redundancy in generating article content again in the left column
        # You might want to remove or adjust this part as it seems to duplicate functionality
        # with left_column: 
        #     if user_query: 
        #         with st.spinner('Fetching sources...'):
        #             time.sleep(20)  # This appears redundant
        #             article_content = generate_article_from_articles(article_thumbnails)
        #             st.markdown(article_content)

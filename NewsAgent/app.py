import streamlit as st
import time
from news_extractor import obtain_articles_from_query
from article_creator import generate_article_from_articles

# Title or introduction to your app
st.title("News Article Generation App")

# Search bar
user_query = st.text_input("Search for stories...", "")

if user_query: 
    # Simulating API call delays
    with st.spinner('Fetching articles...'):
        time.sleep(2)  # Simulate delay of fetching data
        article_thumbnails = obtain_articles_from_query(user_query)
        
    left_column, right_column = st.columns([3, 2])  # 60% - 40% width distribution

    # Assuming article_thumbnails is a list of dictionaries with 'title', 'image', 'summary', 'link'
    if article_thumbnails:
        # Generate article content in the left column
        with left_column:
            with st.spinner('Generating article from sources...'):
                time.sleep(5)  # Simulate article generation time
                article_content = generate_article_from_articles(user_query, article_thumbnails)
                st.markdown(article_content)
                
        # Display article thumbnails in the right column
        with right_column:
            st.write("Sources Found")
            for index, article in enumerate(article_thumbnails):
                # Use column 1 for the first 5 articles, then column 2 for the next 5
                col = st.columns(2)[index % 2]  # This alternates between the first and second column for each article
                with col:
                    st.image(article['top_image'], caption=article['title'])
                    st.write(article['summary'])
                    # Streamlit doesn't support directly opening links from buttons,
                    # so we use a workaround to display the link as text or markdown
                    link = f"[Read More]({article['link']})"
                    st.markdown(link, unsafe_allow_html=True)
                
                # Add a spacer after every 10th article (5 in each column)
                if (index + 1) % 10 == 0:
                    st.write("")  # This could be a spacer
                    
                # Assuming you only want to display the first 10 articles
                if index == 9:
                    break

        with left_column: 
            if user_query: 
                with st.spinner('Fetching sources...'):
                    time.sleep(20)
                    article_content = generate_article_from_articles(article_thumbnails)
                    st.markdown(article_content)

import urllib.request
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import xmltodict
from pandas import json_normalize

st.set_page_config(page_title="A killer read")

st.title("📚 A Killer read 📚")
st.subheader("Compare your Goodreads history to the United Health Care CEO's Killer, Louis Mangione")

default_username = st.selectbox(
    "Use my own Goodreads profile",
    ("89659767-tyler-richards",),
)

st.markdown("**or**")

user_input = st.text_input(
    "Input your own Goodreads Link (e.g. https://www.goodreads.com/user/show/89659767-tyler-richards)"
)

need_help = st.expander("Need help? 👉")
with need_help:
    st.markdown(
        "Having trouble finding your Goodreads profile? Head to the [Goodreads website](https://www.goodreads.com/) and click profile in the top right corner."
    )

if not user_input:
    user_input = f"https://www.goodreads.com/user/show/{default_username}"

user_id = "".join(filter(lambda i: i.isdigit(), user_input))
user_name = user_input.split(user_id, 1)[1].split("-", 1)[1].replace("-", " ")
gr_key = st.secrets["goodreads_key"]

@st.cache_data
def get_user_data(user_id, key=gr_key, v="2", shelf="read", per_page="400"):
    api_url_base = "https://www.goodreads.com/review/list/"
    final_url = (
        api_url_base
        + user_id
        + ".xml?key="
        + key
        + "&v="
        + v
        + "&shelf="
        + shelf
        + "&per_page="
        + per_page
    )
    contents = urllib.request.urlopen(final_url).read()
    return contents

user_input = str(user_input)
contents = get_user_data(user_id=user_id, v="2", shelf="read", per_page="200")
contents = xmltodict.parse(contents)

if int(contents["GoodreadsResponse"]["reviews"]["@total"]) == 0:
    st.write(
        "Looks like you did not read any books on Goodreads. Add some books to your profile or try a different profile"
    )
    st.stop()

df = json_normalize(contents["GoodreadsResponse"]["reviews"]["review"])
df['rating'] = df['rating'].apply(lambda x: None if x == '0' else x)
uhs_reader_df = pd.read_csv("uhs_reader_list.csv")
df['is_read_by'] = df['book.title'].apply(
    lambda x: any(x.lower() in title.lower() or title.lower() in x.lower() 
                 for title in uhs_reader_df['title'])
)

st.subheader(f'What books does {user_name} have in common with the UHS Killer?')

df_common = df[df["is_read_by"] == True]

if len(df_common) == 0:
    st.write("**You have not read any books in common with the UHS Killer.**")
    st.balloons()
    with st.expander("Show all your reads"):
        st.dataframe(df.style.set_properties(**{'text-align': 'left'}))
    with st.expander("Show all the UHS Killer's reads"):
        st.dataframe(uhs_reader_df.style.set_properties(**{'text-align': 'left'}))

else:
    percentage = int((len(df_common)/len(df)*100))
    st.balloons()
    st.write(f"**You have read {len(df_common)} books in common, which is {percentage}% of your reads.**")
    if percentage > 1:
        st.write("**yikes**, maybe you should read some different books?")

    # Create comparison dataframe
    comparison_df = pd.DataFrame()
    comparison_df['Book Title'] = df_common['book.title']
    comparison_df['Your Rating'] = df_common['rating']

    # Match books and get UHS ratings
    def get_uhs_rating(title):
        matches = uhs_reader_df[uhs_reader_df['title'].str.lower().str.contains(title.lower()) | 
                            uhs_reader_df['title'].str.lower().str.contains(title.lower())]
        if matches.empty or 'rating' not in matches.columns:
            return None
        rating = matches['rating'].iloc[0]
        return int(rating) if pd.notnull(rating) else None

    comparison_df["Louis Mangione's Rating"] = comparison_df['Book Title'].apply(get_uhs_rating)

    # Display the comparison table
    comparison_df["Louis Mangione's Rating"] = comparison_df["Louis Mangione's Rating"].apply(lambda x: int(x) if pd.notnull(x) else None)
    st.dataframe(
        comparison_df.style.format({"Louis Mangione's Rating": '{:.0f}'}).set_properties(**{'text-align': 'left'}),
        use_container_width=True,
        column_config={"Book Title": st.column_config.TextColumn(width="medium")}
    )

    #show all the books that you have read
    with st.expander("Show all your reads"):
        df_show = df[['book.title', 'rating']]
        df_show.columns = ['Book Title', 'Your Rating']
        st.dataframe(df_show.style.set_properties(**{'text-align': 'left'}))

    with st.expander("Show all the UHS Killer's reads"):
        uhs_reader_df_show = uhs_reader_df[['title', 'rating']]
        uhs_reader_df_show.columns = ['Book Title', 'Louis Mangione\'s Rating']
        #make sure it is integer or None and format as plain number
        uhs_reader_df_show['Louis Mangione\'s Rating'] = uhs_reader_df_show['Louis Mangione\'s Rating'].apply(lambda x: int(x) if pd.notnull(x) else None)
        st.dataframe(uhs_reader_df_show.style.format({'Louis Mangione\'s Rating': '{:.0f}'}).set_properties(**{'text-align': 'left'}))

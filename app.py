import pandas as pd
import requests
import streamlit as st
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
import base64

# ==== Streamlit Page Config ====
st.set_page_config(page_title="PopFlix", layout="wide")

# ==== Function to Convert Logo to Base64 ====
def get_base64_img(image_path):
    with open(image_path, "rb") as img_file:
        data = img_file.read()
        return base64.b64encode(data).decode()

# ==== Load and Encode Logo ====
logo_base64 = get_base64_img("logo.png")

# ==== Header with Logo and Title ====
st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; margin-top: 10px;">
        <img src="data:image/png;base64,{logo_base64}" style="height: 90px; margin-right: 10px;"/>
        <h1 style="font-size: 64px; margin: 0;">PopFlix</h1>
    </div>
""", unsafe_allow_html=True)

# ==== Tagline ====
st.markdown("""
    <p style='text-align: center; font-size: 24px; margin-top: 10px;'>
        Because scrolling for 45 minutes is a real horror movie.
    </p>
    <p style='text-align: center; font-size: 20px;'>
        Just pick a movie you love — and PopFlix will suggest five similar films, complete with posters and titles.
    </p>
""", unsafe_allow_html=True)

# ==== Dark Mode Toggle ====
dark_mode = st.toggle("🌙 Dark Mode", value=True)
bg_color = "#111" if dark_mode else "#fff"
text_color = "#fff" if dark_mode else "#000"

# ==== Custom CSS Styling ====
st.markdown(f"""
    <style>
        .movie-card {{
            display: inline-block;
            margin: 10px;
            text-align: center;
            background-color: {bg_color};
            color: {text_color};
            padding: 10px;
            border-radius: 12px;
            width: 200px;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .movie-card:hover {{
            transform: scale(1.05);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        }}
        .movie-poster {{
            width: 100%;
            border-radius: 8px;
        }}
        .movie-title {{
            font-size: 18px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .movie-subtext {{
            font-size: 16px;
            margin-top: 6px;
        }}
        .trailer-button {{
            margin-top: 10px;
            display: inline-block;
            padding: 8px 14px;
            border-radius: 6px;
            background-color: #e50914;
            color: white;
            text-decoration: none;
            font-size: 16px;
            font-weight: bold;
        }}
    </style>
""", unsafe_allow_html=True)

# ==== TMDB API Fetch ====
def fetch_movie_metadata(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
        data = requests.get(url).json()
        poster_path = data.get('poster_path')
        imdb_rating = data.get('vote_average', 'N/A')
        genres = ", ".join([genre['name'] for genre in data.get('genres', [])])
        trailer_url = f"https://www.youtube.com/results?search_query={'+'.join(data.get('title', '').split())}+trailer"
        poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image"
        return poster_url, imdb_rating, genres, trailer_url
    except:
        return "https://via.placeholder.com/500x750?text=Error", "N/A", "", "#"

# ==== Load Movies Data ====
@st.cache_data
def load_data():
    df = pd.read_csv("movies.csv")
    df = df[['id', 'title', 'genres', 'keywords', 'cast', 'director', 'overview']]
    df.dropna(inplace=True)
    df['tags'] = df['overview'] + " " + df['genres'] + " " + df['keywords'] + " " + df['cast'] + " " + df['director']
    df['tags'] = df['tags'].str.lower()
    return df

# ==== Compute Similarities ====
@st.cache_data
def get_similarity_matrix(data):
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vector_matrix = cv.fit_transform(data['tags']).toarray()
    similarity = cosine_similarity(vector_matrix)
    return similarity

# ==== Recommendation Logic ====
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(enumerate(similarity[index]), key=lambda x: x[1], reverse=True)[1:6]
    results = []
    for i in distances:
        movie_id = movies.iloc[i[0]].id
        title = movies.iloc[i[0]].title
        poster, rating, genres, trailer = fetch_movie_metadata(movie_id)
        results.append((title, poster, rating, genres, trailer))
    return results

# ==== Main App Execution ====
movies = load_data()
similarity = get_similarity_matrix(movies)

# ==== Custom Label for Selectbox ====
st.markdown("<h3 style='font-size: 26px;'>🎥 Select a movie you like:</h3>", unsafe_allow_html=True)
selected_movie = st.selectbox("", movies['title'].values)

if st.button("✨ Recommend"):
    results = recommend(selected_movie)
    st.subheader("💡 You may also like:")

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.markdown(f"""
                <div class="movie-card">
                    <img src="{results[i][1]}" class="movie-poster" />
                    <div class="movie-title">{results[i][0]}</div>
                    <div class="movie-subtext">⭐ IMDb: {results[i][2]}</div>
                    <div class="movie-subtext">🎭 {results[i][3]}</div>
                    <a class="trailer-button" href="{results[i][4]}" target="_blank">▶ Watch Trailer</a>
                </div>
            """, unsafe_allow_html=True)

# -*- coding: utf-8 -*-
"""
Created on Sun Jul 27 15:23:02 2025

@author: Milad Gh
"""

import requests
import pandas as pd
from config import OMDB_API_KEY

class MovieExplorer:
    def __init__(self):
        self.api_key = OMDB_API_KEY
        self.base_url = "http://www.omdbapi.com/"

    def fetch_movie(self, title):
        params = {
            "t": title.strip(),
            "apikey": self.api_key
            }
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()

            return data
        except Exception as e:
            print("Error:", e)
            return {"Response": "False", "Error": str(e)}

    def save_movie(self, data):
        try:
            rating = float(data.get("imdbRating", 0))
        except ValueError:
            rating = 0

        new_data = {
            "imdbID": data.get("imdbID"),
            "Title": data.get("Title"),
            "Year": data.get("Year"),
            "Genre": data.get("Genre"),
            "IMDB Rating": rating,
            "Plot": data.get("Plot"),
            "Poster": data.get("Poster")
        }

        df_new = pd.DataFrame([new_data])
        try:
            df_existing = pd.read_csv("movies.csv")
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        except FileNotFoundError:
            df_combined = df_new

        df_combined.to_csv("movies.csv", index=False)
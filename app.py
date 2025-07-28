# -*- coding: utf-8 -*-
"""
Created on Sun Jul 27 15:24:00 2025

@author: Milad Gh
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
from movie_explorer import MovieExplorer
from PIL import Image, ImageTk
import requests
from io import BytesIO
import pandas as pd

explorer = MovieExplorer()

saved_movies_container = None

class VerticalScrolledFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        canvas = tk.Canvas(self, borderwidth=0)
        self.frame = tk.Frame(canvas)
        vsb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return

        x = y = 0
        x = self.widget.winfo_rootx() + 30
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # No window decorations
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffcc",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9)
        )
        label.pack(ipadx=5, ipady=2)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def search_movie():
    title = entry.get()
    
    if not title.strip():
        messagebox.showwarning("Warning", "Enter a movie title.")
        return
    
    data = explorer.fetch_movie(title)
    if data.get("Response") == "False":
        messagebox.showerror("Error", f"Movie not found: {data.get('Error')}")
        return

    result_text.config(state='normal')
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, f"🎥 Title: {data.get('Title')}\n")
    result_text.insert(tk.END, f"📅 Year: {data.get('Year')}\n")
    result_text.insert(tk.END, f"🎭 Genre: {data.get('Genre')}\n")
    result_text.insert(tk.END, f"⭐ IMDb Rating: {data.get('imdbRating')}\n")
    result_text.insert(tk.END, f"📝 Plot:\n{data.get('Plot')}\n")
    result_text.config(state='disabled')
    
    save_button.config(state='normal')
    save_button.movie_data = data
    
    # Load and show poster image
    poster_url = data.get("Poster")
    if poster_url and poster_url != "N/A":
        try:
            img_response = requests.get(poster_url)
            img_data = img_response.content
            img = Image.open(BytesIO(img_data))
            img = img.resize((200, 300), Image.LANCZOS)
            poster_image = ImageTk.PhotoImage(img)

            poster_label.config(image=poster_image)
            poster_label.image = poster_image  # Store reference to avoid garbage collection
        except Exception as e:
            print("❌ Failed to load poster:", e)
            poster_label.config(image='', text="Poster not available")
    else:
        poster_label.config(image='', text="Poster not available")
    
def save_movie():
    data = save_button.movie_data
    title = data.get("Title")

    # Check if the movie is already in movies.csv
    try:
        df = pd.read_csv("movies.csv")
        imdb_id = data.get("imdbID")
        if not df[df["imdbID"] == imdb_id].empty:
            messagebox.showinfo("Duplicate", "This movie is already saved.")
            return

        if not df[df["Title"] == title].empty:
            messagebox.showinfo("Duplicate", f"'{title}' is already saved.")
            return
    except FileNotFoundError:
        df = pd.DataFrame()  # No file yet, safe to save

    # Save and refresh
    explorer.save_movie(data)
    show_saved_movies()
    messagebox.showinfo("Saved", f"'{title}' has been saved.")
    
def show_saved_movies():
    global saved_movies_container

    # Remove old saved section if it exists
    if saved_movies_container is not None:
        saved_movies_container.destroy()

    try:
        df = pd.read_csv("movies.csv")
        if df.empty:
            return
    except FileNotFoundError:
        return

    saved_movies_container = tk.LabelFrame(window, text="💾 Saved Movies", font=("Arial", 11, "bold"))
    saved_movies_container.pack(pady=5, fill="both", expand=True)

    # --- Scrollable horizontal canvas ---
    canvas = tk.Canvas(saved_movies_container)
    scrollbar = tk.Scrollbar(saved_movies_container, orient="horizontal", command=canvas.xview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(xscrollcommand=scrollbar.set)

    canvas.pack(side="top", fill="both", expand=True)
    scrollbar.pack(side="bottom", fill="x")

    # Display posters + titles in horizontal row
    for idx, row in df.iterrows():
        try:
            movie_block = tk.Frame(scrollable_frame)
            movie_block.grid(row=0, column=idx, padx=10, pady=0)

            poster_url = row.get("Poster", "")
            # Inside the loop:
            if poster_url and poster_url != "N/A":
                img_data = requests.get(poster_url).content
                img = Image.open(BytesIO(img_data))
                img = img.resize((100, 150), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)

                def on_click_movie(title=row["Title"]):
                    # Refetch full movie data from OMDb 
                    data = explorer.fetch_movie(title)
                    display_movie_details(data)

                img_label = tk.Label(movie_block, image=img_tk, cursor="hand2")
                img_label.image = img_tk
                img_label.pack()
                img_label.bind("<Button-1>", lambda e, t=row["Title"]: on_click_movie(t))
                
                rating = row.get("IMDB Rating", "N/A")
                genre = row.get("Genre", "N/A")
                tooltip_text = f"⭐ Rating: {rating}\n🎭 Genre: {genre}"

                ToolTip(img_label, tooltip_text)

            title_lbl = tk.Label(movie_block, text=row["Title"], wraplength=100, font=("Arial", 8))
            title_lbl.pack()
            
            delete_btn = tk.Button(movie_block, text="🗑 Delete", font=("Arial", 8), fg="red",
                                   command=lambda mid=row["imdbID"]: delete_movie(mid)
                                 )
            delete_btn.pack(pady=2)
        except Exception as e:
            print(f"⚠️ Failed to display saved movie: {e}")
            
def display_movie_details(data):
    if data.get("Response") == "False":
        messagebox.showerror("Error", f"Movie not found: {data.get('Error')}")
        return

    result_text.config(state='normal')
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, f"🎥 Title: {data.get('Title')}\n")
    result_text.insert(tk.END, f"📅 Year: {data.get('Year')}\n")
    result_text.insert(tk.END, f"🎭 Genre: {data.get('Genre')}\n")
    result_text.insert(tk.END, f"⭐ IMDb Rating: {data.get('imdbRating')}\n")
    result_text.insert(tk.END, f"📝 Plot:\n{data.get('Plot')}\n")
    result_text.config(state='disabled')

    # Load poster
    poster_url = data.get("Poster")
    if poster_url and poster_url != "N/A":
        try:
            img_data = requests.get(poster_url).content
            img = Image.open(BytesIO(img_data))
            img = img.resize((200, 300), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)

            poster_label.config(image=img_tk)
            poster_label.image = img_tk
        except Exception as e:
            print("Failed to load poster:", e)
            poster_label.config(image='', text="Poster not available")
    else:
        poster_label.config(image='', text="Poster not available")

    # Store data for Save button
    save_button.config(state='normal')
    save_button.movie_data = data
    
def delete_movie(imdb_id):
    try:
        df = pd.read_csv("movies.csv")

        # Filter out the movie to delete
        df = df[df["imdbID"] != imdb_id]

        df.to_csv("movies.csv", index=False)
        show_saved_movies()  # Refresh saved section
        messagebox.showinfo("Deleted", "Movie has been removed.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete movie: {e}")
    
# --- GUI Setup ---
window = tk.Tk()
window.resizable(False, False)
window.title("🎬 Movie Explorer")
window.geometry("600x600")

main = VerticalScrolledFrame(window)
main.pack(fill="both", expand=True)
window = main.frame

tk.Label(window, text="Enter Movie Title:", font=("Arial", 12)).pack(fill="x", expand=True)
entry = tk.Entry(window, font=("Arial", 12))
entry.pack(fill="x", expand=True, padx=10)

tk.Button(window, text="🔍 Search", command=search_movie, font=("Arial", 11)).pack(fill="x",
                                                    expand=True, padx=10, pady=10)

poster_label = tk.Label(window)
poster_label.pack(pady=10)

result_text = scrolledtext.ScrolledText(window, height=15, font=("Consolas", 10))
result_text.pack(pady=10)
result_text.config(state='disabled')

save_button = tk.Button(window, text="💾 Save Movie", state='disabled', command=save_movie, font=("Arial", 11))
save_button.pack(pady=5)

show_saved_movies()
window.mainloop()
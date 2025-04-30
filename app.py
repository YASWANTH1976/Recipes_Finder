from flask import Flask, render_template, request, redirect, url_for
import requests
import sqlite3
from urllib.parse import quote

app = Flask(__name__)

# Replace with your Spoonacular API key
API_KEY = "3198fafc797a413b85d1660b77f46f1d"

def init_db():
    with sqlite3.connect('favorites.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS favorites
                       (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recipe_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        image TEXT NOT NULL)''')
        conn.commit()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', error=None)

@app.route('/results', methods=['POST'])
def results():
    ingredients = request.form['ingredients'].strip()
    if not ingredients:
        return render_template('index.html', error="Please enter at least one ingredient.")
    
    try:
        url = f"https://api.spoonacular.com/recipes/findByIngredients?apiKey={API_KEY}&ingredients={ingredients}&number=6"
        response = requests.get(url)
        response.raise_for_status()
        recipes = response.json()
        
        if not recipes:
            return render_template('index.html', error="No recipes found for these ingredients.")
        
        # Encode titles and images for URL safety
        for recipe in recipes:
            recipe['encoded_title'] = quote(recipe['title'])
            recipe['encoded_image'] = quote(recipe['image'])
        
        return render_template('results.html', recipes=recipes, ingredients=ingredients)
    except requests.RequestException:
        return render_template('index.html', error="Error fetching recipes. Check your API key or try again.")

@app.route('/recipe/<recipe_id>')
def recipe_details(recipe_id):
    try:
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={API_KEY}&includeNutrition=false"
        response = requests.get(url)
        response.raise_for_status()
        recipe = response.json()
        
        # Fetch video (if available)
        video_url = ""
        if recipe.get('sourceUrl'):
            video_search = f"https://api.spoonacular.com/recipes/{recipe_id}/videos?apiKey={API_KEY}"
            video_response = requests.get(video_search)
            if video_response.status_code == 200:
                videos = video_response.json()
                if videos and videos.get('videos'):
                    video_url = videos['videos'][0].get('youTubeId', '')
                    if video_url:
                        video_url = f"https://www.youtube.com/embed/{video_url}"
        
        # Fetch steps
        steps = []
        if recipe.get('analyzedInstructions'):
            for instruction in recipe['analyzedInstructions']:
                for step in instruction['steps']:
                    steps.append(step['step'])
        
        return render_template('recipe_details.html', recipe=recipe, video_url=video_url, steps=steps, ingredients=','.join([ing['name'] for ing in recipe.get('usedIngredients', [])]))
    except requests.RequestException:
        return render_template('index.html', error="Error fetching recipe details.")

@app.route('/favorites')
def favorites():
    try:
        with sqlite3.connect('favorites.db') as conn:
            favorites = conn.execute('SELECT recipe_id, title, image FROM favorites').fetchall()
        return render_template('favorites.html', favorites=favorites)
    except sqlite3.Error:
        return render_template('index.html', error="Error loading favorites.")

@app.route('/shopping_list/<recipe_id>')
def shopping_list(recipe_id):
    try:
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/ingredientWidget.json?apiKey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        ingredients = response.json().get('ingredients', [])
        return render_template('shopping_list.html', ingredients=ingredients, recipe_id=recipe_id)
    except requests.RequestException:
        return render_template('index.html', error="Error generating shopping list.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
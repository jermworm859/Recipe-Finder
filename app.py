from flask import Flask, render_template, request, redirect, url_for
import requests
import sqlite3
from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

def get_favorited_ids():
    conn = sqlite3.connect('favorites.db')
    cursor = conn.cursor()
    cursor.execute('SELECT meal_id FROM favorites')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

@app.route('/', methods=['GET'])
def home():
    
    # Get search term from URL
    search = request.args.get('search')
    #Pagination
    page = int(request.args.get('page', 1))
    per_page = 5
    meals = []
    total_pages = 0
    
    if search: #Only make API call if user searched for something

        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={search}"

        #Make the API request
        response = requests.get(url)
        data = response.json()
        all_meals = data.get('meals') or []
        total_pages = (len(all_meals) + per_page - 1) // per_page

        start = (page - 1) * per_page
        end = start + per_page
        meals = all_meals[start:end]
    
    # Get list of favorited meal IDs
    favorited_ids = get_favorited_ids
        

    return render_template('index.html', 
                           search=search, 
                           meals=meals,
                           page=page,
                           total_pages=total_pages,
                           favorited_ids=get_favorited_ids())

@app.route('/favorite', methods=['POST'])
def favorite():
    import urllib.parse
    meal_id = request.form['meal_id']
    meal_name = request.form['meal_name']
    meal_thumb = request.form['meal_thumb']
    category = request.form['category']
    area = request.form['area']
    ingredients = request.form['ingredients']

    print(f"Favorite request: id={meal_id}, name={meal_name}, thumb={meal_thumb}")

    conn = sqlite3.connect('favorites.db')
    cursor = conn.cursor()

    try:
        # Insert meal into favorites table if not already there
        cursor.execute('''
            INSERT OR IGNORE INTO favorites (meal_id, meal_name, meal_thumb, category, area, ingredients)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (meal_id, meal_name, meal_thumb, category, area, ingredients))
        conn.commit()
        print("Favorite saved successfully.")
    except Exception as e:
        print(f"Error saving favorite: {e}")
    finally:
        conn.close()
    
    # Redirect back to homepage (preserves search term)
    return redirect(url_for('home'))

@app.route('/favorites')
def view_favorites():

    category_filter = request.args.get('category')
    area_filter = request.args.get('area')

    conn = sqlite3.connect('favorites.db')
    cursor = conn.cursor()

    # Fetch distinct categories and areas
    cursor.execute('SELECT DISTINCT category FROM favorites WHERE category IS NOT NULL')
    categories = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT DISTINCT area FROM favorites WHERE area IS NOT NULL')
    areas = [row[0] for row in cursor.fetchall()]

    # Build the base query
    query = 'SELECT meal_id, meal_name, meal_thumb, ingredients, notes FROM favorites WHERE 1=1'
    params = []

    if category_filter:
        query += ' AND category = ?'
        params.append(category_filter)
    if area_filter:
        query += ' AND area = ?'
        params.append(area_filter)
    
    cursor.execute(query, params)
    favorites = cursor.fetchall()


    #Create meal_notes dictionary: {meal_id: notes}
    meal_notes = {meal_id: notes or '' for meal_id, _, _, _, notes in favorites}


    conn.close()    

    # Send both the favorites and the notes to the template
    return render_template('favorites.html', 
                           favorites=[(meal_id, meal_name, meal_thumb, ingredients) for meal_id, meal_name, meal_thumb, ingredients, _ in favorites],
                           meal_notes=meal_notes,
                           categories=categories,
                           areas=areas,
                           selected_category=category_filter,
                           selected_area=area_filter) 

@app.route('/remove_favorite', methods=['POST'])
def remove_favorite():
    meal_id = request.form['meal_id']

    conn = sqlite3.connect('favorites.db')
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM favorites WHERE meal_id = ?', (meal_id,))
        conn.commit()
    finally:
        conn.close()
    
    return redirect(url_for('view_favorites'))

@app.route('/save_note', methods=['POST'])
def save_note():
    meal_id = request.form['meal_id']
    notes = request.form['notes']

    conn = sqlite3.connect('favorites.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
                       UPDATE favorites
                       SET notes = ?
                       WHERE meal_id = ?
        ''', (notes, meal_id))
        conn.commit()
    finally:
        conn.close()
    
    return redirect(url_for('view_favorites'))



@app.route('/random')
def random_meal():
    url = 'https://www.themealdb.com/api/json/v1/1/random.php'
    response = requests.get(url)
    data = response.json()
    meals = data.get('meals', [])

    return render_template(
        'index.html',
        meals=meals,
        search='Random Meal',
        favorited_ids=get_favorited_ids(),
        page=1,
        total_pages=1
    )

@app.route('/favorites/print')
def print_favorites():
    conn = sqlite3.connect('favorites.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM favorites')
    favorites = cursor.fetchall()
    conn.close()

    return render_template('print_favorites.html', favorites=favorites)
    

@app.route('/export_pdf')
def export_pdf():
    conn = sqlite3.connect('favorites.db')
    cursor = conn.cursor()

    cursor.execute('SELECT meal_name, category, area, ingredients FROM favorites')
    favorites = cursor.fetchall()
    conn.close()

    # Create PDF in memory
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50 #start from top margin

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "My Favorite Recipes")
    y -=30

    pdf.setFont("Helvetica", 12)
    for meal_name, category, area, ingredients in favorites:
        if y < 100: #new page if near bottom
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 12)
        
        pdf.drawString(50, y, f"Meal: {meal_name}")
        y -= 15
        pdf.drawString(50, y, f"Category: {category}, Area: {area}")
        y -= 15
        pdf.drawString(50, y, f"Ingredients: {ingredients}")
        y -= 30
    
    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="favorites.pdf", mimetype='application/pdf')
if __name__ == '__main__':
    app.run(debug=True)
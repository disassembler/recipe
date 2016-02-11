from flask import Flask
from flask import render_template
from flask.ext.pymongo import PyMongo

app = Flask(__name__)
app.config.from_object('config')
mongo = PyMongo(app)

@app.route('/view/<recipe_id>')
def view_recipe(recipe_id):
    recipe = mongo.db.recipes.find_one_or_404({'_id': recipe_id})
    return render_template('view_recipe.html', recipe=recipe)

@app.route('/list')
def list():
    recipes = mongo.db.recipes.find()
    return render_template('list.html', recipes=recipes)

if __name__ == "__main__":
    app.run(host='0.0.0.0')

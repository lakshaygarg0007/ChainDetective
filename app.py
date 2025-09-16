from flask import Flask, render_template, request, jsonify
from model import perform_query_from_ui
from check_fbi_most_wanted import check_fbi_most_wanted

app = Flask(__name__)

criminal_names = ['VincentRomano', 'TommyBugati', 'ElenaMoretti']
@app.route('/')
def hello_world():
    return render_template('index.html', criminal_names=criminal_names)


@app.route('/predict', methods=['POST'])
def predict():
    criminal_name = request.form['criminal']
    query = request.form['query']

    # Call the function to process the query
    result = perform_query_from_ui(query, criminal_name)

    # Return the result to the frontend
    return render_template('index.html', criminal_names=criminal_names, result=result)


@app.route("/fbi-check", methods=["POST"])
def fbi_check():
    data = request.json
    name = data.get("name")
    if not name:
        return jsonify({"error": "missing name"}), 400
    matches = check_fbi_most_wanted(name)
    return jsonify({"matches": matches})


if __name__ == '__main__':
    app.run(debug=True)
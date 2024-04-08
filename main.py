from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if request.method == 'POST':
        data = request.get_json()
        user_message = data['message']

        # Code du ChatBot pour traiter user_message et générer une réponse
        bot_response = "Bonjour, je suis un ChatBot !"

        return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)

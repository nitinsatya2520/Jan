import spacy
import requests
import datetime
import random
import pint
import webbrowser
import wikipedia  # ✅ Add this import
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

nlp = spacy.load('en_core_web_sm')

profiles = {
    "Nitin": {"name": "Nitin", "greeting": "Hello Nitin! How can I assist you today?"}
}

reminders = []

jokes = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!"
]

fun_facts = [
    "Did you know? Honey never spoils.",
    "Fun fact: A day on Venus is longer than a year on Venus."
]

def get_time_based_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif 12 <= hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

def get_weather(command):
    doc = nlp(command)
    city = None
    for ent in doc.ents:
        if ent.label_ == 'GPE':
            city = ent.text
            break

    if not city:
        return "Please specify the city you want the weather for."

    api_key = "03f7fb2a6ffa9af4e20414dc73edb7a3"
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(base_url)
        data = response.json()
        if data['cod'] == 200:
            temperature = data['main']['temp']
            weather_description = data['weather'][0]['description']
            return f"The temperature in {city} is {temperature}°C with {weather_description}."
        else:
            return f"Sorry, I couldn't fetch the weather details for {city}."
    except Exception as e:
        return f"An error occurred while fetching the weather: {e}"

def get_news():
    api_key = "c83f785369614f86b9b145c09b7c5c56"
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"

    try:
        response = requests.get(url)
        data = response.json()
        if data['status'] == 'ok':
            articles = data['articles']
            if articles:
                headlines = [article['title'] for article in articles[:5]]
                news = "Top news headlines: " + ", ".join(headlines)
                return news
            else:
                return "No news articles found."
        else:
            return "Sorry, I couldn't fetch the news."
    except Exception as e:
        return f"An error occurred while fetching the news: {e}"

def add_reminder(reminder):
    reminders.append(reminder)
    return f"Reminder added: {reminder}"

def list_reminders():
    if reminders:
        return "Your reminders:\n" + "\n".join(reminders)
    else:
        return "You have no reminders."

def tell_joke():
    return random.choice(jokes)

def tell_fun_fact():
    return random.choice(fun_facts)

def perform_math(command):
    try:
        result = eval(command)  # ⚠️ Dangerous in production
        return f"The result is {result}"
    except Exception:
        return "Sorry, I couldn't calculate that."

def fallback_web_search(command):
    try:
        summary = wikipedia.summary(command, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Your query is ambiguous. Try one of these: {', '.join(e.options[:5])}"
    except wikipedia.exceptions.PageError:
        # Fall back to Google
        return f"Sorry, I couldn't find any result on Wikipedia. Here's a Google search: https://www.google.com/search?q={command.replace(' ', '+')}"
    except Exception:
        return f"An error occurred. You can try searching here: https://www.google.com/search?q={command.replace(' ', '+')}"

def convert_units(command):
    ureg = pint.UnitRegistry()
    try:
        expression = command.lower().replace("convert", "").strip()
        result = ureg.parse_expression(expression)
        return f"The result is {result:.2f}"
    except Exception:
        return "Sorry, I couldn't convert that."

def handle_command_with_nlp(command):
    command_lower = command.lower()

    if 'weather' in command_lower:
        return get_weather(command_lower)
    elif 'news' in command_lower:
        return get_news()
    elif 'joke' in command_lower:
        return tell_joke()
    elif 'fun fact' in command_lower:
        return tell_fun_fact()
    elif 'calculate' in command_lower:
        math_expression = command_lower.replace('calculate', '').strip()
        return perform_math(math_expression)
    elif 'convert' in command_lower:
        return convert_units(command_lower)
    elif 'remind me to' in command_lower:
        reminder_text = command_lower.replace('remind me to', '').strip()
        return add_reminder(reminder_text)
    elif 'list reminders' in command_lower:
        return list_reminders()
    elif 'who are you' in command_lower or 'your name' in command_lower:
        return "I am JAN, your assistant."
    elif 'time' in command_lower:
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        return f"The current time is {current_time}"
    elif 'date' in command_lower:
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        return f"Today's date is {current_date}"
    elif 'open google' in command_lower:
        return "Opening Google is not supported in text mode."
    elif 'exit' in command_lower or 'quit' in command_lower:
        return "Goodbye!"
    else:
        return fallback_web_search(command)

@app.route('/')
def home():
    return jsonify({"status": "Jan backend is live"})

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.json
    command = data.get('command')
    if command:
        response = handle_command_with_nlp(command)
        return jsonify({"response": response})
    return jsonify({"error": "No command provided"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

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

import wikipedia

def fallback_web_search(command):
    try:
        # Try getting Wikipedia summary and URL
        page = wikipedia.page(command)
        summary = wikipedia.summary(command, sentences=2)
        wiki_url = page.url
        youtube_url = f"https://www.youtube.com/results?search_query={command.replace(' ', '+')}"
        return (
            f"{summary}<br><br>"
            f"🔗 <a href='{wiki_url}' target='_blank'>Read more on Wikipedia</a><br>"
            f"▶️ <a href='{youtube_url}' target='_blank'>Search on YouTube</a>"
        )
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Your query is ambiguous. Try one of these: {', '.join(e.options[:5])}"
    except wikipedia.exceptions.PageError:
        # Wikipedia page not found, fallback to Google and YouTube
        google_url = f"https://www.google.com/search?q={command.replace(' ', '+')}"
        youtube_url = f"https://www.youtube.com/results?search_query={command.replace(' ', '+')}"
        return (
            f"Couldn't find results on Wikipedia.<br><br>"
            f"🔎 <a href='{google_url}' target='_blank'>Search on Google</a><br>"
            f"▶️ <a href='{youtube_url}' target='_blank'>Search on YouTube</a>"
        )
    except Exception:
        google_url = f"https://www.google.com/search?q={command.replace(' ', '+')}"
        youtube_url = f"https://www.youtube.com/results?search_query={command.replace(' ', '+')}"
        return (
            f"An error occurred while searching.<br><br>"
            f"🔎 <a href='{google_url}' target='_blank'>Search on Google</a><br>"
            f"▶️ <a href='{youtube_url}' target='_blank'>Search on YouTube</a>"
        )


        
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
    elif 'google' in command_lower:
        google_query = command_lower.replace('google', '').strip()
        google_url = f"https://www.google.com/search?q={google_query.replace(' ', '+')}"
        return f"Opening Google for '{google_query}' is not supported in text mode."
    elif 'youtube' in command_lower:
        youtube_query = command_lower.replace('youtube', '').strip()
        youtube_url = f"https://www.youtube.com/results?search_query={youtube_query.replace(' ', '+')}"
        return f"Opening YouTube for '{youtube_query}' is not supported in text mode."
    elif 'wikipedia' in command_lower:
        wikipedia_query = command_lower.replace('wikipedia', '').strip()
        return fallback_web_search(wikipedia_query)
    elif any(phrase in command_lower for phrase in ['who is kadavakollu nitin satya', 'who is nitin', 'say about nitin', 'tell me about nitin', 'tell me about yourself', 'about nitin']):
        return (
            "👨‍💻 Kadavakollu Nitin Satya is a passionate tech enthusiast, software developer, and entrepreneur. "
            "He is pursuing a B.Tech in Artificial Intelligence & Data Science with a specialization in Cyber Security, "
            "and also a BBA at KL University. Nitin is the founder of TECHVERRA SOLUTIONS PRIVATE LIMITED, and has worked on projects including AI assistants, "
            "portfolio sites, chat apps, music players, and more.\n\n"
            "🌐 Portfolio: [https://nitinsatya2520.github.io](https://nitinsatya2520.github.io)\n"
            "🐙 GitHub: [https://github.com/nitinsatya2520](https://github.com/nitinsatya2520)\n"
            "📸 Instagram: [https://instagram.com/nitinsatya2520](https://instagram.com/nitinsatya2520)\n"
            "💼 LinkedIn: [https://linkedin.com/in/nitinsatya2520](https://linkedin.com/in/nitinsatya2520)\n"
            "🏢 Company: [https://techverra.in](https://techverra.in)\n\n"
            "He is known for innovation, dedication, and a passion for building impactful solutions."
        )
    elif 'who are you' in command_lower or 'your name' in command_lower:
        return "I am JAN, your personal AI assistant created by Nitin Satya."
    
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

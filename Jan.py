import speech_recognition as sr
import pyttsx3
import os
import spacy
import requests
import datetime
import random
import pint
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import WebDriverException
import threading
import pvporcupine
import pyaudio
import struct
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# Suppress logging errors from pyttsx3
logging.getLogger('pyttsx3').addHandler(logging.NullHandler())

# Initialize spaCy model
nlp = spacy.load('en_core_web_sm')

# Initialize recognizer and speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# User profile for personalized greetings
profiles = {
    "Nitin": {"name": "Nitin", "greeting": "Hello Nitin! How can I assist you today?"}
}

# Reminders and To-Do List storage
reminders = []

# Jokes and Fun Facts
jokes = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!"
]

fun_facts = [
    "Did you know? Honey never spoils.",
    "Fun fact: A day on Venus is longer than a year on Venus."
]

# Function to convert text to speech
def speak(text):
    engine.say(text)
    engine.runAndWait()

def get_image_from_alternate_source(query):
    speak("Showing information related to it.")
    webbrowser.open(f"https://www.google.com/search?q={query}&tbm=isch")  # Image search

def get_entity_info(query):
    api_key = 'YOUR_GOOGLE_KG_API_KEY'  # Replace with your key
    url = f'https://kgsearch.googleapis.com/v1/entities:search?query={query}&key={api_key}&limit=5&indent=True'

    response = requests.get(url).json()

    if 'itemListElement' in response and response['itemListElement']:
        entity = response['itemListElement'][0]['result']
        name = entity.get('name', 'Unknown entity')
        description = entity.get('description', 'No description available.')

        print(f"{name} is {description}.")
        speak(f"{name} is {description}.")

        image_url = entity.get('image', {}).get('url')

        if image_url and any(image_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            webbrowser.open(image_url)
        else:
            print("No valid image URL available for this entity. Fetching from alternate source.")
            get_image_from_alternate_source(query)

        related_entities = entity.get('relatedTopics', [])
        for rel in related_entities:
            rel_name = rel.get('name', 'Unknown')
            rel_image_url = rel.get('image', {}).get('url')
            if rel_image_url and any(rel_image_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                print(f"Opening image for related entity: {rel_name}")
                webbrowser.open(rel_image_url)
            else:
                print(f"No valid image URL for related entity: {rel_name}. Fetching from alternate source.")
                get_image_from_alternate_source(query)
    else:
        print("No information found for the given query.")
        get_image_from_alternate_source(query)
        speak("No information found for the given query.")

def get_weather(command):
    doc = nlp(command)
    city = None
    for ent in doc.ents:
        if ent.label_ == 'GPE':
            city = ent.text
            break

    if not city:
        speak("Please specify the city you want the weather for.")
        return

    api_key = "YOUR_OPENWEATHERMAP_API_KEY"  # Replace with your key
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(base_url)
        data = response.json()

        if data['cod'] == 200:
            temperature = data['main']['temp']
            weather_description = data['weather'][0]['description']
            speak(f"The temperature in {city} is {temperature} degrees Celsius with {weather_description}.")
        else:
            speak(f"Sorry, I couldn't fetch the weather details for {city}.")
    except Exception as e:
        speak(f"An error occurred while fetching the weather: {e}")

def get_time_based_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif 12 <= hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

def get_news():
    api_key = "YOUR_NEWSAPI_API_KEY"  # Replace with your key
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        if data['status'] == 'ok':
            articles = data['articles']
            if articles:
                headlines = [article['title'] for article in articles[:5]]
                news = "Here are the top news headlines: " + ", ".join(headlines)
                speak(news)
            else:
                speak("No news articles found.")
        else:
            speak("Sorry, I couldn't fetch the news.")
    except Exception as e:
        speak(f"An error occurred while fetching the news: {e}")

def add_reminder(reminder):
    reminders.append(reminder)
    speak(f"Reminder added: {reminder}")

def list_reminders():
    if reminders:
        speak("Here are your reminders:")
        for reminder in reminders:
            speak(reminder)
    else:
        speak("You have no reminders.")

def tell_joke():
    joke = random.choice(jokes)
    speak(joke)

def tell_fun_fact():
    fact = random.choice(fun_facts)
    speak(fact)

def perform_math(command):
    try:
        # WARNING: eval() can be unsafe; consider using safer alternatives like sympy
        result = eval(command)
        speak(f"The result is {result}")
    except Exception:
        speak("Sorry, I couldn't calculate that.")

def convert_units(command):
    ureg = pint.UnitRegistry()
    try:
        # Extract everything after "convert"
        expression = command.lower().replace("convert", "").strip()
        result = ureg.parse_expression(expression)
        speak(f"The result is {result:.2f}")
    except Exception as e:
        print(f"Error: {e}")
        speak("Sorry, I couldn't convert that.")

def open_youtube_and_play(command):
    if 'play' in command:
        song_name = command.split('play', 1)[1].strip()
        if song_name:
            threading.Thread(target=play_youtube_song, args=(song_name,), daemon=True).start()
        else:
            speak("Please specify the song you want to play.")
    else:
        speak("Please specify the song you want to play.")

def play_youtube_song(song_name):
    driver = None
    try:
        driver = webdriver.Chrome()
        driver.get("https://www.youtube.com")

        time.sleep(2)
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.send_keys(song_name)
        search_box.send_keys(Keys.RETURN)

        time.sleep(2)
        first_video = driver.find_element(By.XPATH, '//*[@id="video-title"]')
        first_video.click()

        driver.maximize_window()

        # Keep the browser open until closed manually
        while True:
            time.sleep(1)
            try:
                driver.current_url  # just check if browser is alive
            except WebDriverException:
                break

    except Exception as e:
        speak(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()

def open_whatsapp():
    try:
        webbrowser.open("https://web.whatsapp.com/")
        print("Opening WhatsApp Web")
    except Exception as e:
        speak(f"An error occurred while opening WhatsApp: {e}")

def handle_command_with_nlp(command):
    command_lower = command.lower()

    if 'email' in command_lower:
        speak("Do you want to send an email?")
        # Add email logic here if needed

    elif 'weather' in command_lower:
        speak("Fetching weather details...")
        get_weather(command_lower)

    elif 'news' in command_lower:
        speak("Fetching news headlines...")
        get_news()

    elif 'joke' in command_lower:
        tell_joke()

    elif 'fun fact' in command_lower:
        tell_fun_fact()

    elif 'calculate' in command_lower:
        math_expression = command_lower.replace('calculate', '').strip()
        perform_math(math_expression)

    elif 'convert' in command_lower:
        convert_units(command_lower)

    elif 'remind me to' in command_lower:
        reminder_text = command_lower.replace('remind me to', '').strip()
        add_reminder(reminder_text)

    elif 'list reminders' in command_lower:
        list_reminders()

    elif 'who are you' in command_lower:
        speak("I am JAN, your assistant")

    elif 'what is your name' in command_lower or 'your name' in command_lower:
        speak("I am JAN!")

    elif 'open youtube' in command_lower and 'play' in command_lower:
        open_youtube_and_play(command_lower)

    elif 'open notepad' in command_lower:
        speak("Opening Notepad")
        os.system("notepad")

    elif 'open whatsapp' in command_lower:
        speak("Opening WhatsApp Web")
        open_whatsapp()

    elif 'time' in command_lower:
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        speak(f"The current time is {current_time}")

    elif 'date' in command_lower:
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today's date is {current_date}")

    elif 'open google' in command_lower:
        speak("Opening Google")
        webbrowser.open("https://www.google.com")

    elif 'exit' in command_lower or 'quit' in command_lower:
        speak("Goodbye!")
        os._exit(0)  # Immediately exit all threads safely

    else:
        get_entity_info(command_lower)

def listen_for_wake_word():
    porcupine = pvporcupine.create(keywords=["picovoice", "hey google", "jarvis"])
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )
    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected")
                speak("Yes?")
                command = listen_for_command()
                if command:
                    handle_command_with_nlp(command)
    finally:
        audio_stream.close()
        pa.terminate()
        porcupine.delete()

def listen_for_command():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, phrase_time_limit=5)
    try:
        command = recognizer.recognize_google(audio)
        print(f"Recognized: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I did not understand that.")
        return None
    except sr.RequestError:
        print("Request error from Google Speech Recognition service.")
        return None

def main():
    profile_name = "Nitin"
    greeting = get_time_based_greeting()
    if profile_name in profiles:
        speak(profiles[profile_name]["greeting"])
    else:
        speak(f"{greeting}! How can I assist you today?")

    while True:
        command = listen_for_command()
        if command:
            handle_command_with_nlp(command)

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.json
    command = data.get('command')
    if command:
        handle_command_with_nlp(command)
        return jsonify({"response": "Command handled"})
    return jsonify({"error": "No command provided"}), 400

if __name__ == '__main__':
    # Start Flask in background thread
    flask_thread = threading.Thread(target=lambda: app.run(debug=True, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()

    # Start assistant main loop
    main()

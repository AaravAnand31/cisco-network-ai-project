import speech_recognition as sr

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("🎤 Speak now...")
    audio = recognizer.listen(source)

try:
    text = recognizer.recognize_google(audio)

    print("\nYou said:")
    print(text)

except Exception as e:
    print("Error:", e)
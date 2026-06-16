import speech_recognition as sr

def generate_command(text):
    text = text.lower()

    if "show interfaces" in text:
        return "show ip interface brief"

    elif "show version" in text:
        return "show version"

    elif "show running config" in text:
        return "show running-config"

    else:
        return "Unknown command"

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("🎤 Speak now...")
    audio = recognizer.listen(source)

try:
    spoken_text = recognizer.recognize_google(audio)

    print("\nYou said:")
    print(spoken_text)

    command = generate_command(spoken_text)

    print("\nCisco Command:")
    print(command)

except Exception as e:
    print("Error:", e)
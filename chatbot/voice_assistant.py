import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import pyttsx3

model = whisper.load_model("base")
engine = pyttsx3.init()

def record_audio():
    fs = 44100
    seconds = 6
    print("Listening...")
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()
    write("voice.wav", fs, recording)
    print("Recording done")

def speech_to_text():
    record_audio()
    result = model.transcribe("voice.wav")
    return result["text"]

def speak(text):
    engine.say(text)
    engine.runAndWait()

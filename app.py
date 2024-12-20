from flask import Flask, request, jsonify
import base64
import speech_recognition as sr
import io
import wave
from pydub import AudioSegment

app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if not request.is_json:
        return jsonify({"error": "Request must be in JSON format"}), 400

    data = request.get_json()
    if 'audio_data' not in data:
        return jsonify({"error": "Missing 'audio_data' field in JSON"}), 400

    audio_b64 = data['audio_data']

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        return jsonify({"error": "Invalid base64 encoding", "details": str(e)}), 400
    try:
        mp3_io = io.BytesIO(audio_bytes)
        audio_segment = AudioSegment.from_file(mp3_io, format="mp3")
    except Exception as e:
        return jsonify({"error": "Failed to process MP3 data", "details": str(e)}), 400

    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    wav_io.seek(0)
    try:
        with wave.open(wav_io, 'rb') as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
    except wave.Error as e:
        return jsonify({"error": "Failed to process WAV data after conversion", "details": str(e)}), 400

    # Create AudioData from the raw frames in memory
    audio_data = sr.AudioData(frames, sample_rate, sample_width)

    r = sr.Recognizer()
    try:
        recognized_text = r.recognize_google(audio_data)
    except sr.UnknownValueError:
        recognized_text = ""
    except sr.RequestError as e:
        return jsonify({"error": "Speech recognition request failed", "details": str(e)}), 500

    return jsonify({"transcribed_text": recognized_text}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6942)

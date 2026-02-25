import sys
import os
import time
import wave
import threading
import multiprocessing
import pygame
import speech_recognition as sr
import pyttsx3

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QTextBrowser, QLabel, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Import backend chatbot
from assistant import MultilingualChatbot

class LocalTTS:
    """Handles free local TTS for system alerts using pyttsx3 to save Sarvam credits."""
    @staticmethod
    def _speak_process(text):
        """Runs in an isolated process to prevent pyttsx3 COM/threading crashes."""
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.say(text)
        engine.runAndWait()
        
    @staticmethod
    def speak(text):
        """Spawns an isolated process for speech to avoid 'run loop already started'."""
        p = multiprocessing.Process(target=LocalTTS._speak_process, args=(text,))
        p.start()


class WakeWordWorker(QThread):
    """Background listener for the wake word using Speech_Recognition."""
    wake_word_detected = pyqtSignal()
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.is_active = True
        self.wake_words = [
            # Standard
            "hey assistant", "hey optivox", "optivox", 
            # Phonetic mishearings by Google Speech Recognition
            "optimax", "opti works", "optics box", "optimox", 
            "hey optimox", "hey optics box", "hey optics works", 
            "hay optivox", "assistance", "heya sister", "optic box", "optics works"
        ]

    def run(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_active:
                self.status_update.emit("Dormant (Listening for 'Hey Optivox')...")
                try:
                    # Short listen timeout to periodically check if we should stop the thread
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    
                    if not self.is_active:
                        break
                        
                    # Using free Google STT purely for wake word detection to avoid local model complex installations
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"[Debug] Background heard: {text}")
                    
                    for word in self.wake_words:
                        if word in text:
                            # Pause self to trigger recording phase
                            self.is_active = False 
                            self.wake_word_detected.emit()
                            break

                except sr.WaitTimeoutError:
                    continue  # Timeout, keep listening
                except sr.UnknownValueError:
                    continue  # Didn't understand, keep listening
                except sr.RequestError as e:
                    print(f"[Debug] Could not request results: {e}")
                    time.sleep(2)  # Avoid spamming on connection issues
                except Exception as e:
                    print(f"[Debug] Wake word error: {str(e)}")


class AutoRecorderWorker(QThread):
    """Records audio strictly when the user is speaking, clipping out silence."""
    finished_recording = pyqtSignal(str) # Path to saved wav
    error_signal = pyqtSignal(str)
    
    def __init__(self, output_path="user_input.wav"):
        super().__init__()
        self.output_path = output_path
        self.recognizer = sr.Recognizer()

    def run(self):
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise briefly
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen to the user. Phrase time limit ensures it stops if they talk forever.
                # The built-in silence detection (VAD) stops the recording when they pause.
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
                
                # Save specifically using standard 16-bit WAV for the Sarvam API
                with open(self.output_path, "wb") as f:
                    f.write(audio.get_wav_data())
                    
                self.finished_recording.emit(self.output_path)
                
        except sr.WaitTimeoutError:
            self.error_signal.emit("Timeout: No speech detected.")
        except Exception as e:
            self.error_signal.emit(f"Recording error: {str(e)}")


class BotWorker(QThread):
    """Background thread to process audio using MultilingualChatbot APIs."""
    update_chat = pyqtSignal(str, str) # role (user/bot), message
    processing_status = pyqtSignal(str) # Status updates
    finished_processing = pyqtSignal(str) # Path to the bot audio file to play
    error_signal = pyqtSignal(str)

    def __init__(self, chatbot, input_audio_path):
        super().__init__()
        self.chatbot = chatbot
        self.input_audio_path = input_audio_path

    def run(self):
        try:
            self.processing_status.emit("Transcribing...")
            
            # Step 1: STT
            transcribed_text = self.chatbot.transcribe_audio(self.input_audio_path)
            if not transcribed_text:
                self.error_signal.emit("Transcription failed or no speech detected.")
                return

            self.update_chat.emit("You", transcribed_text)
            self.processing_status.emit("Thinking...")

            # Step 2: Get chat response
            response_data = self.chatbot.get_chat_response(transcribed_text)
            bot_text = response_data['response']
            lang = response_data['language']
            
            self.update_chat.emit(f"Bot ({lang})", bot_text)
            self.processing_status.emit("Generating audio...")

            # Step 3: TTS
            output_file = "bot_reply.wav"
            lang_code = self.chatbot.lang_code_map.get(lang, "en-IN")
            
            success = self.chatbot.text_to_speech(bot_text, output_file, lang_code)
            if success:
                self.finished_processing.emit(output_file)
            else:
                self.error_signal.emit("Audio generation failed.")

        except Exception as e:
            self.error_signal.emit(f"An error occurred: {str(e)}")


class VoiceAssistantUI(QMainWindow):
    playback_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # API Key
        API_KEY = "sk_abg9n10d_IDjWXi9iDwAMYhS65sWOBWpO"
        self.chatbot = MultilingualChatbot(API_KEY)
        
        # Audio Player Init
        pygame.mixer.init()
        self.input_wav = "user_input.wav"
        
        self.wake_worker = None
        self.auto_recorder = None
        
        self.playback_finished.connect(self.resume_dormancy)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Optivox Voice Assistant")
        self.setGeometry(300, 300, 500, 650)
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #2ecc71; padding: 10px;")
        layout.addWidget(self.status_label)
        
        # Hands-Free Toggle
        self.hands_free_cb = QCheckBox("Enable Hands-Free Mode (Wake Word)")
        self.hands_free_cb.setFont(QFont("Arial", 10))
        self.hands_free_cb.setStyleSheet("QCheckBox { color: #f1c40f; padding-bottom: 5px;}")
        self.hands_free_cb.stateChanged.connect(self.toggle_hands_free)
        layout.addWidget(self.hands_free_cb)
        
        # Chat History
        self.chat_browser = QTextBrowser()
        self.chat_browser.setFont(QFont("Arial", 11))
        self.chat_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #34495e;
                border: 2px solid #7f8c8d;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.chat_browser.append("<b>System:</b> Voice Assistant initialized.<br><i>Click the button to speak, or enable Hands-Free mode to automatically wake up on 'Hey Optivox'.</i>")
        layout.addWidget(self.chat_browser)
        
        # Record Button
        self.record_btn = QPushButton("🎙️ Click to Auto-Record")
        self.record_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; /* Orange when idle */
                color: white;
                border: none;
                border-radius: 20px;
                padding: 20px;
            }
            QPushButton:disabled {
                background-color: #27ae60; /* Green when processing/replying */
            }
        """)
        
        # We changed this to a simple click since Auto-VAD handles the silence detection
        self.record_btn.clicked.connect(self.manual_start_recording)
        
        layout.addWidget(self.record_btn)
        central_widget.setLayout(layout)

    def toggle_hands_free(self, state):
        if state == Qt.Checked:
            self.start_wake_word_listener()
        else:
            self.stop_wake_word_listener()
            self.reset_ui()

    def start_wake_word_listener(self):
        if self.wake_worker is None or not self.wake_worker.isRunning():
            self.wake_worker = WakeWordWorker()
            self.wake_worker.wake_word_detected.connect(self.on_wake_word)
            self.wake_worker.status_update.connect(self.update_status)
            self.wake_worker.start()
            
            self.record_btn.setEnabled(False)
            self.record_btn.setText(" Hands-Free Active ")
            self.record_btn.setStyleSheet("QPushButton { background-color: #7f8c8d; color: white; border-radius: 20px; padding: 20px; }")

    def stop_wake_word_listener(self):
        if self.wake_worker:
            self.wake_worker.is_active = False
            self.wake_worker = None

    def on_wake_word(self):
        """Triggered automatically via background thread."""
        self.stop_playback()
        # Local free TTS to acknowledge wake up without spending API credits
        threading.Thread(target=LocalTTS.speak, args=("Yes?",), daemon=True).start()
        # Start the Auto-Recorder immediately
        self.start_auto_recording(triggered_by_wake=True)

    def manual_start_recording(self):
        """Triggered when the user manually pushes the button."""
        self.stop_playback()
        self.stop_wake_word_listener() # Interrupt hands-free if manually interacting
        self.start_auto_recording(triggered_by_wake=False)

    def start_auto_recording(self, triggered_by_wake=False):
        self.status_label.setText("🔴 Listening...")
        self.status_label.setStyleSheet("color: #e74c3c; padding: 10px;")
        
        self.record_btn.setEnabled(False)
        self.record_btn.setText("🔴 Recording... (Speak now)")
        self.record_btn.setStyleSheet("QPushButton { background-color: #c0392b; color: white; border-radius: 20px; padding: 20px; }")
        
        self.auto_recorder = AutoRecorderWorker(self.input_wav)
        self.auto_recorder.finished_recording.connect(self.process_recording)
        self.auto_recorder.error_signal.connect(self.handle_error)
        self.auto_recorder.start()

    def process_recording(self, saved_path):
        self.status_label.setText("Processing...")
        self.status_label.setStyleSheet("color: #f1c40f; padding: 10px;")
        
        self.record_btn.setText("⏳ Processing...")
        self.record_btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; border-radius: 20px; padding: 20px; }")
        
        if saved_path and os.path.exists(saved_path):
            self.worker = BotWorker(self.chatbot, saved_path)
            self.worker.update_chat.connect(self.append_chat)
            self.worker.processing_status.connect(self.update_status)
            self.worker.finished_processing.connect(self.play_response)
            self.worker.error_signal.connect(self.handle_error)
            self.worker.start()
        else:
            self.handle_error("No audio recorded.")

    def append_chat(self, role, message):
        color = "#3498db" if role == "You" else "#2ecc71"
        self.chat_browser.append(f"<b style='color:{color}'>{role}:</b> {message}")
        # Scroll to bottom smoothly
        self.chat_browser.verticalScrollBar().setValue(self.chat_browser.verticalScrollBar().maximum())

    def update_status(self, status):
        self.status_label.setText(status)

    def handle_error(self, error_msg):
        self.append_chat("System Error", error_msg)
        # Instead of Sarvam TTS to report errors, we use the free local TTsx3 engine!
        threading.Thread(target=LocalTTS.speak, args=("An error occurred.",), daemon=True).start()
        
        # Schedule reset on the main UI thread after a brief delay
        threading.Timer(1.0, self.playback_finished.emit).start()

    def stop_playback(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    def play_response(self, audio_path):
        self.status_label.setText("🔊 Playing response...")
        self.status_label.setStyleSheet("color: #3498db; padding: 10px;")
        self.record_btn.setText("🔊 Speaking...")
        
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Start a thread to wait for playback to finish, then clean up
            threading.Thread(target=self.wait_and_cleanup, args=(audio_path,), daemon=True).start()
        except Exception as e:
            self.handle_error(f"Could not play audio: {e}")

    def wait_and_cleanup(self, audio_path):
        # Wait until pygame finishes playing the audio
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        pygame.mixer.music.unload()
        time.sleep(0.1)
        
        # Cleanup temp audio files
        for temp_file in [self.input_wav, audio_path]:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Cleanup error for {temp_file}: {e}")
                
        # Re-enable the UI
        self.playback_finished.emit()

    def resume_dormancy(self):
        """Called automatically when processing or playback finishes."""
        if self.hands_free_cb.isChecked():
            self.start_wake_word_listener()
        else:
            self.reset_ui()

    def reset_ui(self):
        if not self.hands_free_cb.isChecked():
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: #2ecc71; padding: 10px;")
            self.record_btn.setEnabled(True)
            self.record_btn.setText("🎙️ Click to Auto-Record")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22; 
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 20px;
                }
            """)

    def closeEvent(self, event):
        self.stop_wake_word_listener()
        pygame.mixer.quit()
        event.accept()

if __name__ == "__main__":
    # Needed for multiprocessing on Windows
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    window = VoiceAssistantUI()
    window.show()
    sys.exit(app.exec_())

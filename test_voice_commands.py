import pytest
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

# Ensure QApplication is created once
if not QCoreApplication.instance():
    app = QApplication(sys.argv)

from voice_assistant.ui_assistant import BotWorker

class MockChatbot:
    @property
    def lang_code_map(self):
        return {"english": "en-IN"}

    def get_chat_response(self, text):
        return {"response": "Mocked response", "language": "english"}

    def text_to_speech(self, text, output_path, language_code):
        return True

def test_botworker_magnifier_command():
    bot = MockChatbot()
    # Test text trigger for magnifier
    worker = BotWorker(bot, input_text="please start magnifier now")
    
    emitted_commands = []
    worker.command_signal.connect(lambda cmd: emitted_commands.append(cmd))
    
    worker.run() # Call run directly for synchronous behavior
    
    assert len(emitted_commands) == 1
    assert emitted_commands[0] == "magnifier"

def test_botworker_reader_command():
    bot = MockChatbot()
    # Test text trigger for reader
    worker = BotWorker(bot, input_text="hey optivox open reader")
    
    emitted_commands = []
    worker.command_signal.connect(lambda cmd: emitted_commands.append(cmd))
    
    worker.run()
    
    assert len(emitted_commands) == 1
    assert emitted_commands[0] == "reader"

def test_botworker_normal_chat():
    bot = MockChatbot()
    worker = BotWorker(bot, input_text="how are you")
    
    emitted_commands = []
    emitted_chat = []
    worker.command_signal.connect(lambda cmd: emitted_commands.append(cmd))
    worker.update_chat.connect(lambda role, msg: emitted_chat.append((role, msg)))
    
    worker.run()
    
    assert len(emitted_commands) == 0 # Command shouldn't be triggered
    
    assert len(emitted_chat) == 2
    assert emitted_chat[0] == ("You", "how are you")
    assert emitted_chat[1] == ("Bot (english)", "Mocked response")

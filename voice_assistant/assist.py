import speech_recognition as sr
import pyttsx3
import time

class VoiceAssistant:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Text-to-speech settings (engine created per call)
        self.speech_rate = 150
        self.speech_volume = 0.9
        
        # Control flag
        self.should_stop = False
        
        # Knowledge base for different topics
        self.knowledge_base = {
            
            'fibonacci': {
                'methods': ['Recursive', 'Iterative', 'Dynamic Programming', 'Matrix Exponentiation'],
                'best': 'Dynamic Programming',
                'descriptions': {
                    'Recursive': 'Simple but inefficient approach that calls itself repeatedly. Time complexity: O(2^n). Good for learning but not practical for large numbers.',
                    'Iterative': 'Uses a loop to calculate Fibonacci numbers. Time complexity: O(n), Space: O(1). Efficient and easy to understand.',
                    'Dynamic Programming': 'Stores previously calculated values to avoid redundant calculations. Time complexity: O(n), Space: O(n). Best balance of clarity and efficiency.',
                    'Matrix Exponentiation': 'Uses matrix multiplication for very fast calculation. Time complexity: O(log n). Best for very large Fibonacci numbers but complex to implement.'
                }
            },
            'sorting': {
                'methods': ['Bubble Sort', 'Quick Sort', 'Merge Sort', 'Heap Sort'],
                'best': 'Quick Sort',
                'descriptions': {
                    'Bubble Sort': 'Simple comparison-based algorithm. Time complexity: O(n²). Good for small datasets or educational purposes only.',
                    'Quick Sort': 'Divide and conquer algorithm. Average time complexity: O(n log n). Best general-purpose sorting algorithm with good cache performance.',
                    'Merge Sort': 'Stable divide and conquer algorithm. Time complexity: O(n log n). Best when stability is required or for linked lists.',
                    'Heap Sort': 'Uses heap data structure. Time complexity: O(n log n). Best when memory is limited as it sorts in-place.'
                }
            },
            'searching': {
                'methods': ['Linear Search', 'Binary Search', 'Hash Table Search'],
                'best': 'Binary Search',
                'descriptions': {
                    'Linear Search': 'Checks each element sequentially. Time complexity: O(n). Best for unsorted small arrays.',
                    'Binary Search': 'Divides sorted array in half repeatedly. Time complexity: O(log n). Best for sorted arrays with frequent searches.',
                    'Hash Table Search': 'Uses hash function for direct access. Time complexity: O(1) average. Best when you need fastest possible lookups and have memory available.'
                }
            }
        }
    
    def stop(self):
        """Set flag to stop the assistant"""
        self.should_stop = True
    
    def speak(self, text):
        """Convert text to speech"""
        if self.should_stop:
            return
            
        print(f"Assistant: {text}")
        try:
            # Create a fresh engine instance for each speech
            engine = pyttsx3.init()
            engine.setProperty('rate', self.speech_rate)
            engine.setProperty('volume', self.speech_volume)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine  # Clean up
        except Exception as e:
            print(f"Speech error: {e}")
            print(f"Assistant (text only): {text}")
    
    def listen(self):
        """Listen to user's voice and convert to text"""
        if self.should_stop:
            return None
            
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                if self.should_stop:
                    return None
                    
                print("Processing...")
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                if not self.should_stop:
                    self.speak("I didn't hear anything. Please try again.")
                return None
            except sr.UnknownValueError:
                if not self.should_stop:
                    self.speak("Sorry, I couldn't understand that. Please speak clearly.")
                return None
            except sr.RequestError:
                if not self.should_stop:
                    self.speak("Sorry, there's an issue with the speech recognition service.")
                return None
    
    def identify_topic(self, query):
        """Identify which topic the user is asking about"""
        for topic in self.knowledge_base.keys():
            if topic in query:
                return topic
        return None
    
    def handle_query(self, query):
        """Main logic to handle user queries"""
        if self.should_stop:
            return
            
        topic = self.identify_topic(query)
        
        if topic:
            data = self.knowledge_base[topic]
            methods = data['methods']
            best_method = data['best']
            
            # Tell about available methods
            methods_list = ", ".join(methods[:-1]) + f", and {methods[-1]}"
            self.speak(f"For {topic}, there are {len(methods)} main methods: {methods_list}.")
            
            if self.should_stop:
                return
            
            # Suggest the best one
            self.speak(f"The best method is generally {best_method}, as it offers the best balance of efficiency and practicality.")
            
            if self.should_stop:
                return
            
            # Ask which one they want to learn about
            self.speak("Which method would you like to know more about?")
            
            # Listen for user's choice
            choice = self.listen()
            
            if choice and not self.should_stop:
                # Find the matching method
                selected_method = None
                for method in methods:
                    if method.lower() in choice:
                        selected_method = method
                        break
                
                if selected_method:
                    description = data['descriptions'][selected_method]
                    self.speak(f"Here's information about {selected_method}: {description}")
                else:
                    self.speak("I didn't catch which method you chose. Please try again.")
        else:
            self.speak("I'm not sure about that topic. I can help you with Fibonacci series, sorting algorithms, or searching algorithms.")
    
    def run_with_flag(self, is_running_func):
        """Main loop to run the assistant with external control flag"""
        self.should_stop = False
        self.speak("Hello! I'm your voice assistant. You can ask me about topics like Fibonacci series, sorting algorithms, or searching algorithms.")
        
        while is_running_func() and not self.should_stop:
            self.speak("What would you like to know?")
            query = self.listen()
            
            if self.should_stop or not is_running_func():
                break
            
            if query:
                if 'exit' in query or 'quit' in query or 'bye' in query:
                    self.speak("Goodbye! Have a great day!")
                    break
                
                self.handle_query(query)
            
            time.sleep(1)
        
        print("Voice assistant loop ended")
    
    def run(self):
        """Main loop to run the assistant (standalone version)"""
        self.should_stop = False
        self.speak("Hello! I'm your voice assistant. You can ask me about topics like Fibonacci series, sorting algorithms, or searching algorithms.")
        
        while not self.should_stop:
            self.speak("What would you like to know?")
            query = self.listen()
            
            if query:
                if 'exit' in query or 'quit' in query or 'bye' in query:
                    self.speak("Goodbye! Have a great day!")
                    break
                
                self.handle_query(query)
            
            time.sleep(1)

# Run the voice assistant
if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
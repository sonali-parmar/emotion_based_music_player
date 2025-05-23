import tkinter as tk
from deepface import DeepFace
import cv2
from PIL import Image, ImageTk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pygame

# Emotion to music mapping
emotion_music_map = {
    'happy': 'happy bollywood songs',
    'sad': 'sad hindi songs',
    'angry': 'motivational workout songs',
    'neutral': 'chill instrumental',
    'fear': 'calming instrumental',
    'surprise': 'feel good bollywood'
}

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="4c676720fc164c3ab541a702690869ac",
                                               client_secret="client_secret",
                                               redirect_uri="http://localhost:8888/callback",
                                               scope="user-library-read user-read-playback-state user-modify-playback-state"))

class EmotionMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Emotion-Based Music Player")
        self.root.geometry("500x700")
        self.root.config(bg="#444444")

        self.cap = None
        self.running = False
        self.frame = None
        self.current_emotion = None
        self.track_list = []
        self.current_index = 0

        # Title
        self.label = tk.Label(root, text="Emotion-Based Music Player", width=30, pady=15, bg="#444444", fg="white", font=("Arial", 16, "bold"))
        self.label.pack(pady=10)

        # Fixed-size frame to hold the video label
        self.video_frame = tk.Frame(root, width=500, height=300, bg="black")
        self.video_frame.pack(pady=10)
        self.video_frame.pack_propagate(False)  # Prevent frame from resizing to contents

        # Label inside that frame
        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.pack(fill="both", expand=True)

        # Frame for Start/Stop buttons
        button_frame = tk.Frame(root, bg="#444444")
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="Start Camera To Detect Emotion", command=self.start_camera,bg="#444444", fg="white",activebackground="green")
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(button_frame, text="Stop Camera To Play Music", command=self.stop_camera,bg="#444444", fg="white",activebackground="red")
        self.stop_button.pack(side=tk.LEFT,padx=10)

        # Song Recommendation UI
        self.song_frame = tk.Frame(root, bg="#444444")
        self.song_frame.pack(pady=20)

        self.prev_button = tk.Button(self.song_frame, text="⏮️ Prev", command=self.prev_song, bg="#222222", fg="white")
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.song_label = tk.Label(self.song_frame, text="Song Recommendation", bg="#666666", fg="white", width=40)
        self.song_label.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(self.song_frame, text="Next ⏭️", command=self.next_song, bg="#222222", fg="white")
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Emotion detection
        self.detect_button = tk.Button(root, text="Detect Emotion and Play Music", command=self.detect_emotion)
        self.detect_button.pack(pady=20)

        # Frame for Pause/Resume buttons
        music_control_frame = tk.Frame(root)
        music_control_frame.pack(pady=10)

        # Pause and Resume
        self.play_button = tk.Button(music_control_frame, text="▶️ Play", command=self.play_music, bg="#333333", fg="white")
        self.play_button.pack(side=tk.LEFT, padx=10)

        self.pause_button = tk.Button(music_control_frame, text="⏸️ Pause", command=self.pause_music, bg="#333333", fg="white")
        self.pause_button.pack(side=tk.LEFT, padx=10)

        # Initialize pygame for audio playback
        pygame.mixer.init()

    def start_camera(self):
        if not self.running:
            self.cap = cv2.VideoCapture(0)
            self.running = True
            self.start_button.config(bg='green') 
            self.update_frame()

    def stop_camera(self):
        if self.running:
            self.running = False
            if self.cap:
                self.cap.release()
            self.start_button.config(bg='#444444')

    def update_frame(self):
        if self.running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame  # Save last frame
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)
                img = img.resize((500, 300))  # Force consistent size
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
        if self.running:
            self.root.after(10, self.update_frame)
        elif self.frame is not None:
            # Display the last frame when stopped
            rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            img = img.resize((500, 300))  # Keep same size
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

    def detect_emotion(self):
        if self.frame is None:
            self.label.config(text="Start the camera first.")
            return
        
        result = DeepFace.analyze(self.frame, actions=['emotion'], enforce_detection=False)
        self.current_emotion = result[0]['dominant_emotion']
        self.label.config(text="Dominant emotion: " + self.current_emotion)
        self.query = emotion_music_map.get(self.current_emotion, "indian songs")
        self.track_list = self.search_spotify(self.query)
        self.current_index = 0
        self.update_song_label()
        self.play_music()

    def search_spotify(self, query):
        # Search for tracks on Spotify based on the emotion
        results = sp.search(query, limit=5, type='track')
        tracks = [track['uri'] for track in results['tracks']['items']]
        return tracks

    def update_song_label(self):
        if self.track_list:
            track_info = sp.track(self.track_list[self.current_index])
            track_name = track_info['name']
            artist_name = track_info['artists'][0]['name']
            self.song_label.config(text=f"🎵 Now Playing: {track_name} by {artist_name}")

    def play_music(self):
        if self.track_list:
            track_uri = self.track_list[self.current_index]
            sp.start_playback(uris=[track_uri])
            pygame.mixer.music.load("temp_audio.mp3")  # Load the temp MP3 from Spotify's download (if possible)
            pygame.mixer.music.play()

    def pause_music(self):
        pygame.mixer.music.pause()

    def next_song(self):
        if self.track_list:
            self.current_index = (self.current_index + 1) % len(self.track_list)
            self.update_song_label()
            self.play_music()

    def prev_song(self):
        if self.track_list:
            self.current_index = (self.current_index - 1) % len(self.track_list)
            self.update_song_label()
            self.play_music()

# Start the application
root = tk.Tk()
app = EmotionMusicPlayer(root)
root.mainloop()

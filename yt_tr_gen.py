import os
import eyed3
from mutagen.flac import FLAC
from pydub import AudioSegment
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# Global variables
selected_directory = ""
use_custom_track_numbers = False
a_side_tracks = 0
b_side_tracks = 0
tracklist = ""

def generate_tracklist(button):
    global selected_directory, use_custom_track_numbers, a_side_tracks, b_side_tracks, tracklist

    if not selected_directory:
        buffer = console.get_buffer()
        buffer.insert(buffer.get_end_iter(), "Please select a directory.\n")
        return
    
    if use_custom_track_numbers:
        if a_side_tracks <= 0:
            buffer = console.get_buffer()
            buffer.insert(buffer.get_end_iter(), "Please enter a valid number of tracks for side A.\n")
            return
        
        if b_side_tracks <= 0:
            buffer = console.get_buffer()
            buffer.insert(buffer.get_end_iter(), "Please enter a valid number of tracks for side B.\n")
            return
    
    tracklist = generate_tracklist_from_directory(selected_directory, use_custom_track_numbers, a_side_tracks, b_side_tracks)
    buffer = console.get_buffer()
    buffer.insert(buffer.get_end_iter(), tracklist)

def generate_tracklist_from_directory(directory, use_custom_track_numbers=False, a_side_tracks=0, b_side_tracks=0):
    tracklist = ""
    total_duration = 0
    track_number = 1
    side = "A"  # Initial side

    files = sorted(os.listdir(directory))
    artists = get_artist(directory)  # Get the unique artist names
    multiple_artists = len(artists) > 1  # Check if there are multiple artists

    for file in files:
        if file.endswith(('.mp3', '.flac')):
            filepath = os.path.join(directory, file)
            
            # Load the audio file's tags using eyed3 for MP3 files
            if file.endswith('.mp3'):
                audiofile = eyed3.load(filepath)
                artist = audiofile.tag.artist
                title = audiofile.tag.title
            else:  # For FLAC files
                audiofile = FLAC(filepath)
                artist = audiofile.get('artist', None)
                title = audiofile.get('title', None)
            
            # Format the trackname as "artist - title" if available, otherwise use the filename
            if multiple_artists:
                trackname = f"{artist} - {title}" if artist and title else file
            else:
                trackname = title if title else file
            
            # Get the duration of the audio file
            duration = get_duration(filepath)
            
            # Get the timestamp for the current track
            timestamp = get_timestamp(total_duration)
            
            # Append the track information to the tracklist string with modified track number and side
            if use_custom_track_numbers:
                if side == "A":
                    tracklist += f"{side}{track_number}. {trackname} {timestamp}\n"
                    if track_number == a_side_tracks:
                        side = "B"  # Switch to side B after A side tracks
                elif side == "B":
                    b_track_number = track_number - a_side_tracks
                    tracklist += f"{side}{b_track_number}. {trackname} {timestamp}\n"
                    if b_track_number == b_side_tracks:
                        side = "A"  # Switch back to side A after B side tracks
            else:
                tracklist += f"{track_number:02d}. {trackname} {timestamp}\n"
            
            # Update the total duration and track number
            total_duration += duration
            track_number += 1

    return tracklist


def get_duration(filepath):
    if filepath.endswith('.mp3'):
        audio = AudioSegment.from_file(filepath)
        duration = len(audio) / 1000  # Duration in seconds
    else:  # For FLAC files
        audio = FLAC(filepath)
        duration = audio.info.length  # Duration in seconds
    return duration


def get_timestamp(duration):
    minutes = int(duration / 60)
    seconds = duration % 60
    return f"{minutes:02d}:{seconds:05.2f}"


def get_artist(directory):
    artists = set()

    files = sorted(os.listdir(directory))
    for file in files:
        if file.endswith(('.mp3', '.flac')):
            filepath = os.path.join(directory, file)
            
            # Load the audio file's tags using eyed3 for MP3 files
            if file.endswith('.mp3'):
                audiofile = eyed3.load(filepath)
                artist = audiofile.tag.artist
            else:  # For FLAC files
                audiofile = FLAC(filepath)
                artist = audiofile.get('artist', None)
            
            if artist:
                artists.add(artist)
    
    return artists


def select_directory(button):
    global selected_directory
    dialog = Gtk.FileChooserDialog(title="Select a directory", parent=window, action=Gtk.FileChooserAction.SELECT_FOLDER)
    dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        selected_directory = dialog.get_filename()
        buffer = console.get_buffer()
        buffer.insert(buffer.get_end_iter(), f"Selected directory: {selected_directory}\n")
    dialog.destroy()


def toggle_custom_track_numbers(checkbox):
    global use_custom_track_numbers
    use_custom_track_numbers = checkbox.get_active()


def set_a_side_tracks(entry):
    global a_side_tracks
    a_side_tracks = int(entry.get_text())


def set_b_side_tracks(entry):
    global b_side_tracks
    b_side_tracks = int(entry.get_text())


def save_tracklist(button):
    global tracklist
    if not tracklist:
        buffer = console.get_buffer()
        buffer.insert(buffer.get_end_iter(), "No tracklist generated.\n")
        return
    
    dialog = Gtk.FileChooserDialog(title="Save Tracklist", parent=window, action=Gtk.FileChooserAction.SAVE)
    dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
    
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        filename = dialog.get_filename()
        with open(filename, "w") as file:
            file.write(tracklist)
        buffer = console.get_buffer()
        buffer.insert(buffer.get_end_iter(), f"Tracklist saved as: {filename}\n")
    dialog.destroy()


# Create the main window
window = Gtk.Window(title="Youtube Tracklist Generator")
window.set_default_size(800, 600)
window.connect("destroy", Gtk.main_quit)

# Create a box for the main layout
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
box.set_border_width(10)
window.add(box)

# Create a box for the directory selection
directory_box = Gtk.Box(spacing=10)
box.pack_start(directory_box, False, False, 0)

# Create a label for the directory selection
directory_label = Gtk.Label(label="Select a directory:")
directory_box.pack_start(directory_label, False, False, 0)

# Create a button to select the directory
directory_button = Gtk.Button.new_with_label("Browse")
directory_button.connect("clicked", select_directory)
directory_box.pack_start(directory_button, False, False, 0)

# Create a box for the custom track numbers checkbox
custom_track_numbers_box = Gtk.Box(spacing=10)
box.pack_start(custom_track_numbers_box, False, False, 0)

# Create a custom track numbers checkbox
custom_track_numbers_checkbox = Gtk.CheckButton(label="Use custom track numbers (A1, A2, B1, B2)")
custom_track_numbers_checkbox.connect("toggled", toggle_custom_track_numbers)
custom_track_numbers_box.pack_start(custom_track_numbers_checkbox, False, False, 0)

# Create a box for the A side tracks input
a_side_tracks_box = Gtk.Box(spacing=10)
box.pack_start(a_side_tracks_box, False, False, 0)

# Create a label for the A side tracks input
a_side_tracks_label = Gtk.Label(label="Number of Tracks on Side A:")
a_side_tracks_box.pack_start(a_side_tracks_label, False, False, 0)

# Create an entry field for the A side tracks input
a_side_tracks_entry = Gtk.Entry()
a_side_tracks_entry.connect("changed", set_a_side_tracks)
a_side_tracks_box.pack_start(a_side_tracks_entry, False, False, 0)

# Create a box for the B side tracks input
b_side_tracks_box = Gtk.Box(spacing=10)
box.pack_start(b_side_tracks_box, False, False, 0)

# Create a label for the B side tracks input
b_side_tracks_label = Gtk.Label(label="Number of Tracks on Side B:")
b_side_tracks_box.pack_start(b_side_tracks_label, False, False, 0)

# Create an entry field for the B side tracks input
b_side_tracks_entry = Gtk.Entry()
b_side_tracks_entry.connect("changed", set_b_side_tracks)
b_side_tracks_box.pack_start(b_side_tracks_entry, False, False, 0)

# Create a box for the generate button
button_box = Gtk.Box(spacing=10)
box.pack_start(button_box, False, False, 0)

# Create a generate button
generate_button = Gtk.Button.new_with_label("Generate")
generate_button.connect("clicked", generate_tracklist)
button_box.pack_start(generate_button, False, False, 0)

# Create a box for the console
console_box = Gtk.Box(spacing=10)
box.pack_start(console_box, True, True, 0)

# Create a label for the console
console_label = Gtk.Label(label="Console:")
console_box.pack_start(console_label, False, False, 0)

# Create a scrolled text widget for the console
console = Gtk.TextView()
console.set_editable(False)
console.set_wrap_mode(Gtk.WrapMode.WORD)
scrolled_window = Gtk.ScrolledWindow()
scrolled_window.set_hexpand(True)
scrolled_window.set_vexpand(True)
scrolled_window.add(console)
console_box.pack_start(scrolled_window, True, True, 0)

# Set the GTK dark mode
style_provider = Gtk.CssProvider()
style_provider.load_from_data(b"""
    GtkWindow, GtkLabel {
        color: #FFFFFF;
        background-color: #202124;
    }
    GtkButton {
        color: #FFFFFF;
        background-color: #404244;
    }
    GtkEntry, GtkTextView {
        color: #FFFFFF;
        background-color: #303134;
    }
    GtkCheckButton {
        color: #FFFFFF;
        background-color: #202124;
    }
""")
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

# Create a box for the save button
save_box = Gtk.Box(spacing=10)
box.pack_start(save_box, False, False, 0)

# Create a save button
save_button = Gtk.Button.new_with_label("Save Tracklist")
save_button.connect("clicked", save_tracklist)
save_box.pack_start(save_button, False, False, 0)

# Show the window
window.show_all()

# Start the main loop
Gtk.main()

from moviepy.editor import AudioFileClip, ImageClip, TextClip, CompositeVideoClip, VideoClip
from PIL import Image
import os
import numpy as np
import pandas as pd
import shutil
import numba as nb
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

# render settings
render_sample = True
render_sample_video = render_sample
render_video = not render_sample
video_fps = 24
video_resolution = '1080p'  # '720p', '1080p', '4k'
core_count = os.cpu_count()

# background settings
background_color = [17, 51, 0]  # RGB color for the background
bg_ball_count = 6
balls_bounce = False  # True for balls bouncing off each other, False for bouncing off walls only
last_t = 0
total_t = 0

# layouts to render
layouts = ['landscape-1', 'portrait-1']
audios = []

# set script directory and file
directory = {'script': {'type': 'script', 'path': os.path.dirname(os.path.realpath(__file__))}}
file = {'script': {'type': 'script', 'path': os.path.realpath(__file__)}}

files_in_audio = {}

# get all other directories
directory['new'] = {'type': 'essential', 'path': os.path.join(directory['script']['path'], 'new')}
directory['layouts'] = {'type': 'essential', 'path': os.path.join(directory['script']['path'], 'layouts')}
directory['processed'] = {'type': 'other', 'path': os.path.join(directory['script']['path'], 'processed')}
directory['failed'] = {'type': 'other', 'path': os.path.join(directory['script']['path'], 'failed')}

# expand on layouts and audio (new) directories
for folder_name in os.listdir(directory['layouts']['path']):
        if folder_name in layouts:
            directory[folder_name] = {'type': 'layout', 'path': os.path.join(directory['layouts']['path'], folder_name)}

for folder_name in os.listdir(directory['new']['path']):
        directory[folder_name] = {'type': 'audio', 'path': os.path.join(directory['new']['path'], folder_name)}

# check essentials directories exist and create missing directories
for key, value in directory.items():
    if (value['type'] == 'essential' or value['type'] == 'layout') and not os.path.isdir(value['path']):
        print('ERROR: "' + value['path'] + '" | Directory not found. Exiting.')
        exit()
    elif not os.path.isdir(value['path']):
        print('WARNING: "' + value['path'] + '" | Directory not found. Creating.')
        os.mkdir(value['path'])
        if not os.path.isdir(value['path']):
            print('ERROR: "' + value['path'] + '" | Directory could not be created. Resuming without creating directory.')
        else:
            print('INFO: "' + directory + '" | Directory created.')

# print list of directories and read files in that directory
print('\nPROGRAM DIRECTORIES:')
for key, value in directory.items():
    if value['type'] == 'essential' or value['type'] == 'other':
        print(' - ' + key.upper() + ': ' + value['path'])

print('\nLAYOUT DIRECTORIES:')
for key, value in directory.items():
    if value['type'] == 'layout':
        print(' - ' + key.upper() + ': ' + value['path'])
        file[key] = {'type': 'layout', 'path': os.path.join(value['path'], 'layout.csv')}
        if not os.path.isfile(file[key]['path']):
            print('   - ERROR: "' + file[key]['path'] + '" | File not found. This layout will not be rendered.')
            layouts.remove(key)
            directory.pop(key)
            file.pop(key)
        else:
            print('   - INFO: "' + file[key]['path'] + '" | Layout file found.')

            # read layout files and check all layout specific images exist
            layout_df = pd.read_csv(file[key]['path'])
            for index, row in layout_df.iterrows():
                if row['type'] == 'image':
                    if row['folder'] == 'layout':
                        file[row['name']] = {'type': 'image', 'path': os.path.join(value['path'], row['img_file'])}
                    
                        if not os.path.isfile(os.path.join(value['path'], row['img_file'])):
                            print('   - ERROR: "' + file[row['name']]['path'] + '" | File required by layout not found. This layout will not be rendered.')
                            layouts.remove(key)
                            directory.pop(key)
                            file.pop(key)
                            break
                        else:
                            print('   - INFO: "' + file[row['name']]['path'] + '" | File required by layout found.')

                    if row['folder'] == 'audio':
                        files_in_audio[row['name']] = {'type': 'image', 'filename': row['img_file']}
                        print('   - INFO: "' + files_in_audio[row['name']]['filename'] + '" | File will be checked in each audio folder.')

if len(layouts) == 0:
    print('\nERROR: No layouts could be rendered. Exiting.')
    exit()

print('\nAUDIO DIRECTORIES:')
for key, value in directory.items():
    if value['type'] == 'audio':
        print(' - ' + key.upper() + ': ' + value['path'])

        file[key] = {'type': 'audio', 'audio-path': os.path.join(value['path'], 'audio.mp3'), 'lyrics-path': os.path.join(value['path'], 'lyrics.csv')}
        
        # check that audio file exists
        if not os.path.isfile(file[key]['audio-path']):
            print('   - ERROR: "' + file[key]['audio-path'] + '" | Audio file not found. This audio will not be rendered.')
            directory.pop(key)
            file.pop(key)
            break
        else:
            print('   - INFO: "' + file[key]['audio-path'] + '" | Audio file found.')

            # check that lyrics file exists
            if not os.path.isfile(file[key]['lyrics-path']):
                print('   - ERROR: "' + file[key]['lyrics-path'] + '" | Lyrics file not found. This audio will not be rendered.')
                directory.pop(key)
                file.pop(key)
                # THIS MEANS THAT WITHOUT LYRICS, THE AUDIO WILL NOT BE RENDERED
                break
            else:
                print('   - INFO: "' + file[key]['lyrics-path'] + '" | Lyrics file found.')
        
                # read layout files check all layout files for the audio exists
                for files in files_in_audio:
                    file_path = os.path.join(value['path'], files_in_audio[files]['filename'])
                    if not os.path.isfile(file_path):
                        print('   - ERROR: "' + file_path + '" | File required by layout not found. This audio will not be rendered.')
                        directory.pop(key)
                        file.pop(key)
                        break
                    else:
                        print('   - INFO: "' + file_path + '" | File required by layout found.')
                        audios.append(key)

if len(audios) == 0:
    print('\nERROR: No audio files could be rendered. Exiting.')
    exit()

# show render settings
print('\nRENDER SETTINGS:')
print(' - Render video: ' + str(render_video))
print(' - Render sample: ' + str(render_sample))
print(' - Video FPS: ' + str(video_fps))
print(' - Video resolution: ' + video_resolution)

# confirm from user if it's ok to proceed with rendering
# if input('\nOk to go ahead? (type "no" to cancel): ').lower() == 'no':
#    exit()

# Set video resolution
def get_dimensions(option):
    switch = {
        '720p': (1280, 720),
        '1080p': (1920, 1080),
        '4K': (3840, 2160),
        '4k': (3840, 2160)
    }
    return switch.get(option, (1920, 1080))  # Default to 1080p if option is not found

video_width, video_height = get_dimensions(video_resolution)

# render video files
for key, value in directory.items():

    if value['type'] == 'audio':
        print('\nNOW PROCESSING: ' + key)

        # read data for clips
        df = pd.read_csv(file[key]['lyrics-path'])
        audio_clip = AudioFileClip(file[key]['audio-path'])

        # get the value from column 2 of the row where the first column is equal to key; this how the lyrics.csv file is structured
        def get_value(dataframe, key, col):
            return dataframe[dataframe.iloc[:, 0] == key].iloc[0, col]

        title = get_value(df, 'title', 1)
        voice = get_value(df, 'voice', 1)
        writer = get_value(df, 'writer', 1)

        # Filter rows where the first column is 'language' and drop columns 2 and 3
        language_row = df[df.iloc[:, 0] == 'language']
        language_row = language_row.drop(language_row.columns[[0, 1, 2]], axis=1)

        # discard more than 3 languages
        if language_row.shape[1] > 3:
            language_row = language_row.iloc[:, :3]

        # do the same for language directions
        lang_dir_row = df[df.iloc[:, 0] == 'lang_dir']
        lang_dir_row = lang_dir_row.drop(lang_dir_row.columns[[0, 1, 2]], axis=1)
        
        if lang_dir_row.shape[1] > 3:
            lang_dir_row = lang_dir_row.iloc[:, :3]

        # count again
        language_count = language_row.shape[1]

        # Filter rows where the first column is 'lyrics'
        lyrics_df = df[df.iloc[:, 0] == 'lyrics']

        # Keep only the first language_count + 2 columns (which represent start and end time)
        lyrics_df = lyrics_df.iloc[:, :(language_count + 3)].drop(lyrics_df.columns[[0]], axis=1)

        # save the number of languages for later
        language_count = lyrics_df.shape[1] - 2     # First two columns are start and end time

        # ALL DATA LOADED FOR THIS AUDIO FILE
        
        def create_composite(layout_name):

            global video_width, video_height, lyrics_df

            layout_clips = []
            layout_df = pd.read_csv(file[layout_name]['path'])
            layout_type = get_value(layout_df, 'layout_type', 1)
            
            if layout_type == 'portrait':
                video_width, video_height = video_height, video_width
            
            layout_rf = video_height / get_value(layout_df, 'layout_type', 7)

            # Add the background clip
            # background draw functions
            @nb.njit
            def update_balls(balls: np.ndarray, dt: float):
                global balls_bounce

                # balls -> [[x, y, r, g, b, radius, vx, vy]]
                for b in range(balls.shape[0]):
                    radius = balls[b, 5]
                    # move
                    balls[b, 0:2] += balls[b, 6:8] * dt * 80
                    
                    # bounce x
                    if balls[b, 0] < radius:
                        balls[b, 6] = np.abs(balls[b, 6])
                    elif balls[b, 0] > video_height - radius:
                        balls[b, 6] = -np.abs(balls[b, 6])

                    # bounce y
                    if balls[b, 1] < radius:
                        balls[b, 7] = np.abs(balls[b, 7])
                    elif balls[b, 1] > video_width - radius:
                        balls[b, 7] = -np.abs(balls[b, 7])

                    # bounce from others
                    if balls_bounce == True:
                        for b2 in range(balls.shape[0]):
                            if b2 == b:
                                continue
                            delta = balls[b, 0:2] - balls[b2, 0:2]
                            dist2 = delta[0] * delta[0] + delta[1] * delta[1]
                            rad2 = balls[b, 5] + balls[b2, 5]
                            rad2 *= rad2

                            if dist2 < rad2:
                                balls[b, 6:8] = delta / np.max(np.abs(delta))

            @nb.njit(parallel=True)
            def draw_balls(screen: np.ndarray, balls: np.ndarray, background_color: tuple):
                w, h = screen.shape[0], screen.shape[1]
                b_count = balls.shape[0]

                # Set parameters for glow
                glow_size = 100
                glow_factor = 10
                max_brightness = 0.2  # Maximum brightness limit (adjust as needed)

                # to use all core_count
                for start in nb.prange(core_count):
                    # for each pixel on screen
                    for x in range(start, w, core_count):
                        for y in range(h):
                            screen[x, y] = background_color  # Fill the screen with background color
                            # for each ball
                            for b in range(b_count):
                                # get ball data from array
                                bx, by = balls[b, 0], balls[b, 1]
                                radius = balls[b, 5]
                                rgb = [1, 1, 1]  # Set ball color to white (RGB: 1, 1, 1)

                                # calculate distance from pixel to ball center
                                dx, dy = x - bx, y - by
                                distance_squared = dx * dx + dy * dy

                                # calculate glow intensity
                                # glow_intensity = radius * radius / (distance_squared + glow_size)
                                glow_intensity = np.exp(-distance_squared / (2 * glow_size * glow_size))

                                # add glow to the pixel color, but limit the maximum brightness
                                for c in range(3):
                                    screen[x, y, c] += min(rgb[c] * glow_intensity * 255.0 * glow_factor, 255 * max_brightness)

            def create_balls(n_balls):
                # make random balls
                balls = np.empty((n_balls, 8), dtype=np.float32)
                for i in range(balls.shape[0]):
                    # generate ball
                    min_size = 25
                    max_size = 30

                    # set size and startiing position
                    radius = np.random.randint(min_size, max_size)
                    x, y = np.random.randint(radius, video_width - radius), np.random.randint(radius, video_height - radius)
                    
                    # set color
                    color = [1,1,1]

                    # set velocity
                    vel = np.random.rand(2)
                    vel = vel / vel.max()

                    # put ball to array
                    balls[i, 0], balls[i, 1] = x, y
                    balls[i, 2:5] = color
                    balls[i, 5] = radius
                    balls[i, 6:8] = vel
                return balls

            balls = create_balls(bg_ball_count)

            def make_frame(t):
                global last_t
                
                screen_arr = np.zeros((video_height, video_width, 3), dtype=np.int32)  # Array for drawing
                
                # Calculate elapsed time since last frame
                dt = t - last_t

                # Check if the elapsed time corresponds to the desired frame rate
                update_balls(balls, dt)  # Update based on actual elapsed time
                last_t = t  # Update the time of the last frame
                
                # Fill the screen with the background color
                screen_arr[:, :] = background_color
                
                draw_balls(screen_arr, balls, background_color)  # Draw balls on the array
                
                return np.clip(screen_arr, 0, 255).astype('uint8')  # Clip and convert to uint8
            
            bg_clip = VideoClip(make_frame, duration=audio_clip.duration)
            layout_clips.append(bg_clip)

            # Iterate over each row
            for index, row in layout_df.iterrows():
                # Render based on the 'type' column
                if row['type'] == 'image':
                    if row['folder'] == 'audio':
                        clip_image = Image.open(os.path.join(directory[key]['path'], row['img_file']))
                    elif row['folder'] == 'layout':
                        clip_image = Image.open(os.path.join(directory[layout_name]['path'], row['img_file']))

                    if (clip_image.mode == 'P'):
                        clip_image = clip_image.convert('RGBA')
                        
                    clip_image = clip_image.resize((int(row['width'] * layout_rf), int(row['height'] * layout_rf)))
                    clip_image = np.array(clip_image)
                    clip_image = ImageClip(clip_image).set_position((int(row['x'] * layout_rf), int(row['y'] * layout_rf)))
                    clip_image = clip_image.set_duration(audio_clip.duration)
                    layout_clips.append(clip_image)

                elif row['type'] == 'rectangle':
                    render_rect = True
                    
                    if row['name'] == 'rec_lyrics' and (language_count < 1 ):     
                        render_rect = False
                    elif row['name'] == 'rec_lang1' and (language_count < 2 ):
                        render_rect = False
                    elif row['name'] == 'rec_lang2' and (language_count < 3):
                        render_rect = False

                    if render_rect == True:
                        clip_rect = Image.new("RGBA", (int(row['width'] * layout_rf), int(row['height'] * layout_rf)), (int(row['r']), int(row['g']), int(row['b']), int(row['a'])))
                        clip_rect = ImageClip(np.array(clip_rect), duration=audio_clip.duration, ismask=False).set_position((int(row['x'] * layout_rf), int(row['y'] * layout_rf)))
                        clip_rect = clip_rect.set_duration(audio_clip.duration)
                        layout_clips.append(clip_rect)

                elif row['type'] == 'text':
                    text = row['name']

                    if row['name'] == 'var_title':
                        text = title
                    elif row['name'] == 'var_voice':
                        text = voice
                    elif row['name'] == 'var_writer':
                        text = writer
                    elif row['name'] == 'lbl_lyrics':
                        if lyrics_df.shape[1] >= 1 + 2:   # +2 because of start and end time
                            text = "Lyrics in " + language_row.iloc[0, 0]
                            text = text.upper()
                        else:
                            text = ""
                    elif row['name'] == 'lbl_lang1':
                        if lyrics_df.shape[1] >= 2 + 2:    # +2 because of start and end time
                            text = "Translation in " + language_row.iloc[0, 1]
                            text = text.upper()
                        else:
                            text = ""
                    elif row['name'] == 'lbl_lang2':
                        if lyrics_df.shape[1] >= 3 + 2:    # +2 because of start and end time
                            text = "Translation in " + language_row.iloc[0, 2]
                            text = text.upper()
                        else:
                            text = ""

                    if not text == "":
                        clip_text = TextClip(text, fontsize=row['size'] * layout_rf, color=row['color'], font=row['font'], align='West', size=(int(row['width'] * layout_rf), None), method='caption')
                        clip_text = clip_text.set_position((int(row['x'] * layout_rf), int(row['y'] * layout_rf)))
                        layout_clips.append(clip_text)

                elif row['type'] == 'lyrics':
                    # Replace NaN values with an empty string
                    lyrics_df = lyrics_df.fillna('')

                    lyric_col = -1
                    
                    if row['name'] == 'var_lyrics' and language_count >= 1:
                        lyric_col = 0 + 2
                    elif row['name'] == 'var_lang1' and language_count >= 2:
                        lyric_col = 1 + 2
                    elif row['name'] == 'var_lang2' and language_count >= 3:
                        lyric_col = 2 + 2

                    if lyric_col >= 0:
                        for index, lyric_row in lyrics_df.iterrows():
                            lyric = lyric_row[lyric_col]
                            lang_dir = lang_dir_row.iloc[0, lyric_col - 2]              # -2 because of start and end time
                            
                            text_dir = 'West'
                            if lang_dir == 'rtl':
                                text_dir = 'East'

                            if lyric and not lyric.isspace():
                                clip_lyric = TextClip(lyric, fontsize=row['size'] * layout_rf, color=row['color'], font=row['font'], align=text_dir, size=(int(row['width'] * layout_rf), None), method='caption')
                                clip_lyric = clip_lyric.set_start(lyric_row['start']).set_end(lyric_row['end']).set_position((int(row['x'] * layout_rf), int(row['y'] * layout_rf))).crossfadein(0.5).crossfadeout(0.5)
                                layout_clips.append(clip_lyric)
                    
            # Create a composite clip
            return CompositeVideoClip(layout_clips, (video_width, video_height)).set_audio(audio_clip)
            # return layout_clips

        for layout in layouts:
            print ('PROCESSING: "' + key + '" | Compositing video using layout: ' + layout)
            last_t = 0
            total_t = 0
            video = create_composite(layout)
            # video = CompositeVideoClip(create_composite(layout), (video_width, video_height)).set_audio(audio_clip)
            video.duration = audio_clip.duration

            if render_sample:
                print ('SAVING: "' + key + ' (' + layout + ' - ' + video_resolution + ').png" | Preview file')
                video.save_frame(os.path.join(value['path'], key + ' (' + layout + ' - ' + video_resolution + ').png'), t=np.random.uniform(100, audio_clip.duration))

            if render_sample_video:
                print ('RENDERING: "' + key + ' (' + layout + ' - ' + video_resolution + ').mp4" | Sample video file')
                video.duration = 10
                video.write_videofile(os.path.join(value['path'], key + ' (' + layout + ' - ' + video_resolution + ').mp4'), fps=video_fps, threads=core_count)

            if render_video:
                print ('RENDERING: "' + key + ' (' + layout + ' - ' + video_resolution + ').mp4" | Video file')
                video.write_videofile(os.path.join(value['path'], key + ' (' + layout + ' - ' + video_resolution + ').mp4'), fps=video_fps, threads=core_count)
            
        if render_video:
            # Move the folder to the processed directory
            print ('MOVING: "' + value['path'] + '" | To processed folder')
            shutil.move(value['path'], directory['processed']['path'])
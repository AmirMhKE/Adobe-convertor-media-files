import subprocess
import os
import shutil
import sys

VID = "screenshare" 
AUD = "cameraVoip"

def get_video_duration_in_seconds(video_path):
    command = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration_str = result.stdout.decode().strip()
    try:
        duration = float(duration_str)
        return duration
    except ValueError:
        return None
    
def get_video_and_audio_files():
    video_s, audio_s = [], []
    for file in os.listdir():
        if file.startswith(VID) and file.endswith("flv"):
            video_s.append(file)
        if file.startswith(AUD) and file.endswith("flv"):
            audio_s.append(file)

    files = video_s + audio_s
    files.sort(key=lambda x: int(x.split("_")[1] + x.split("_")[2].split(".")[0]))
    return files

def final_merge(parts, has_last=False):
    print("Step 3: Started!")
    if has_last:
        temp_name = f"2_part_{len(parts)}.mp4"

        if parts[-1].startswith("a"):
            os.system(f"ffmpeg -f lavfi -i color=c=black -i {parts[-1]} \
                      -c:v libx264 -c:a aac -shortest {temp_name}")
        else:
            os.system(f"ffmpeg -i {parts[-1]} -c:v libx264 -c:a aac {temp_name}")
        parts[-1] = temp_name 

    with open("parts.txt", "w") as pt:
        for pti in parts:
            pt.write(f"file \'{pti}\'\n")

    os.chdir("../")
    if len(parts) > 1:
        os.system("ffmpeg -f concat -i __Temp/parts.txt output.mp4")
    else:
        shutil.copy("__Temp/" + parts[0], "./")
        os.rename(parts[0], "output.mp4")
    os.system("rm -rf __Temp/")
    print("Step 3: Finished! -> output.mp4")

def second_merge(parts):
    result = []
    n = len(parts)
    print("Step 2: Started!")
    os.chdir("__Temp/")

    for i in range(0, n, 2):
        if i == n - 1:
            break
        temp_aud = parts[i] if parts[i].startswith("a") else parts[i + 1]
        temp_vid = parts[i] if parts[i].startswith("v") else parts[i + 1]
        dur1 = get_video_duration_in_seconds(temp_aud)
        dur2 = get_video_duration_in_seconds(temp_vid)
        
        dur_dist = 0
        if dur1 is not None and dur2 is not None:
            dur_dist = int(abs(dur1 - dur2))
        else:
            dur1, dur2 = 0, 0

        name = f"2_part_{i // 2}.mp4"
        if dur1 >= dur2:
            os.system(f"ffmpeg -itsoffset {dur_dist} -i {temp_vid} -i {temp_aud} \
                    -map 0:v:0 -map 1:a:0 -c:v libx264 -c:a aac {name}")
        else:
            os.system(f"ffmpeg -i {temp_vid} -itsoffset {dur_dist} -i {temp_aud} \
                    -map 0:v:0 -map 1:a:0 -c:v libx264 -c:a aac {name}")
        result.append(name)

    print("Step 2: Finished!")
    if n % 2 == 1:
        result.append(parts[-1])
        final_merge(result, True)
    else:
        final_merge(result)

def first_merge():
    files = get_video_and_audio_files()
    parts = [[]]
    result = []
    print("Step 1: Started!")

    last_cond = files[0].split("_")[0]
    start_cond = last_cond

    for file in files:
        temp_cond = file.split("_")[0]
        if last_cond != temp_cond:
            last_cond = temp_cond
            parts.append([].copy())
        parts[-1].append(file)

    for i in range(len(parts)):
        with open("__Temp/temp_part.txt", "w") as tp:
            for pti in parts[i]:
                tp.write(f"file \'../{pti}\'\n")

        temp_out = "" 
        if (i % 2 == 0 and start_cond == AUD) or (i % 2 == 1 and start_cond == VID):
            temp_out += "a_"
        else:
            temp_out += "v_"
        temp_out += "1_part_" + str(i) + ".flv"

        if len(parts[i]) > 1:
            os.system("ffmpeg -safe 0 -f concat -i __Temp/temp_part.txt __Temp/" + temp_out)
        else:
            shutil.copy(parts[i][0], "__Temp/")
            os.rename("__Temp/" + parts[i][0], "__Temp/" + temp_out)
        result.append(temp_out)

    print("Step 1: Finished!")
    second_merge(result)

if __name__ == "__main__":
    path = ""
    try:
        path = sys.argv[1]
    except IndexError:
        path = os.getcwd()
    os.chdir(path)

    if os.path.exists("__Temp/"):
        os.system("rm -rf __Temp/")
    os.mkdir("__Temp/")
    first_merge()

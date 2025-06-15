from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import os
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple
import traceback
import re
import calendar
import random
# from gpt4all import GPT4All # Commented out for Gemini API
import google.generativeai as genai # Added for Gemini API

# Load environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-pro') # Initialize Gemini model

# Initialize GPT4All # Commented out
# print("Initializing GPT4All model...") # Commented out
# model = GPT4All("mistral-7b-instruct-v0.1.Q4_0.gguf") # Commented out
# print("Model initialized successfully") # Commented out

app = FastAPI()

# Initialize geopy
geolocator = Nominatim(user_agent="event_chatbot")

# API Configuration
TICKETMASTER_API_KEY = os.getenv('TICKETMASTER_API_KEY', 'NcUvrnDN536mgv3soGAziWR6KNalhfno')
TICKETMASTER_API_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

# Event-related keywords that trigger event search
EVENT_KEYWORDS = {
    'event', 'events', 'happening', 'concert', 'concerts', 'show', 'shows', 
    'bored', 'things to do', 'plans', 'activities', 'activity', 'fun',
    'tonight', 'weekend', 'tomorrow', 'festival', 'party', 'entertainment',
    'anything', 'sure', 'yes', 'yeah', 'ok', 'okay', 'fine', 'please',
    'what', 'whats', "what's", 'tell', 'show'
}

# Add conversation-related keywords and responses
CONVERSATION_STARTERS = {
    'hi', 'hello', 'hey', 'howdy', 'greetings', 'good morning', 'good afternoon', 'good evening',
    'sup', 'yo', 'hiya', 'hi there', 'hello there'
}

MOOD_KEYWORDS = {
    'bored': ["I can help you find something fun to do! What kind of activities interest you?",
              "Feeling bored? Let's find you something exciting! What's your usual idea of fun?",
              "I know just the cure for boredom - let's discover some events! What interests you?"],
    'lonely': ["Sometimes company makes everything better. Would you like to find some social events?",
               "How about we look for some community events where you could meet new people?",
               "There are lots of group activities happening - would you like to explore some options?"],
    'tired': ["Looking for something relaxing? There might be some nice low-key events nearby.",
              "Sometimes a change of scenery helps. Would you like to see what calm activities are available?",
              "How about we look for some peaceful events, like art galleries or music performances?"],
    'excited': ["That's great! Let's channel that energy into something fun! What are you in the mood for?",
                "Awesome! I know lots of exciting events. What kind of activities get you most pumped?",
                "Love that enthusiasm! Want to see what amazing events are coming up?"],
    'stressed': ["Sometimes a good event can help take your mind off things. Would you like some suggestions?",
                 "How about we look for something relaxing? Music, art, or maybe some outdoor events?",
                 "I know some great stress-relieving activities. Would you like to explore some options?"]
}

INTEREST_KEYWORDS = {
    'music': ["What kind of music do you usually enjoy?",
             "Are you into any particular genre?",
             "There's usually a great music scene around here. What styles do you prefer?"],
    'sports': ["Are you more into watching sports or participating?",
              "Any particular sports you're interested in?",
              "There are lots of sporting events coming up. What's your favorite sport?"],
    'art': ["Do you enjoy creating art or viewing it?",
            "There are some interesting art events happening. What kind of art speaks to you?",
            "Are you interested in any particular style of art?"],
    'food': ["Are you a foodie? There are some great food events happening!",
             "What kind of cuisine do you enjoy most?",
             "There are some interesting food festivals coming up. Would you like to know more?"],
    'outdoor': ["Do you prefer active outdoor events or more relaxed nature activities?",
                "There are some great outdoor events happening. What kind of outdoor activities interest you?",
                "Would you like to hear about some outdoor adventures?"]
}

# Add list of allowed cities
ALLOWED_CITIES = {
    "aberdeen", "abilene", "akron", "albany", "albuquerque", "alexandria", "allentown", "amarillo", "anaheim",
    "anchorage", "ann arbor", "antioch", "apple valley", "appleton", "arlington", "arvada", "asheville", "athens",
    "atlanta", "atlantic city", "augusta", "aurora", "austin", "bakersfield", "baltimore", "barnstable", "baton rouge",
    "beaumont", "bel air", "bellevue", "berkeley", "bethlehem", "billings", "birmingham", "bloomington", "boise",
    "boise city", "bonita springs", "boston", "boulder", "bradenton", "bremerton", "bridgeport", "brighton",
    "brownsville", "bryan", "buffalo", "burbank", "burlington", "cambridge", "canton", "cape coral", "carrollton",
    "cary", "cathedral city", "cedar rapids", "champaign", "chandler", "charleston", "charlotte", "chattanooga",
    "chesapeake", "chicago", "chula vista", "cincinnati", "clarke county", "clarksville", "clearwater", "cleveland",
    "college station", "colorado springs", "columbia", "columbus", "concord", "coral springs", "corona", "corpus christi",
    "costa mesa", "dallas", "daly city", "danbury", "davenport", "davidson county", "dayton", "daytona beach",
    "deltona", "denton", "denver", "des moines", "detroit", "downey", "duluth", "durham", "el monte", "el paso",
    "elizabeth", "elk grove", "elkhart", "erie", "escondido", "eugene", "evansville", "fairfield", "fargo",
    "fayetteville", "fitchburg", "flint", "fontana", "fort collins", "fort lauderdale", "fort smith",
    "fort walton beach", "fort wayne", "fort worth", "frederick", "fremont", "fresno", "fullerton", "gainesville",
    "garden grove", "garland", "gastonia", "gilbert", "glendale", "grand prairie", "grand rapids", "grayslake",
    "green bay", "greenbay", "greensboro", "greenville", "gulfport-biloxi", "hagerstown", "hampton", "harlingen",
    "harrisburg", "hartford", "havre de grace", "hayward", "hemet", "henderson", "hesperia", "hialeah", "hickory",
    "high point", "hollywood", "honolulu", "houma", "houston", "howell", "huntington", "huntington beach",
    "huntsville", "independence", "indianapolis", "inglewood", "irvine", "irving", "jackson", "jacksonville",
    "jefferson", "jersey city", "johnson city", "joliet", "kailua", "kalamazoo", "kaneohe", "kansas city",
    "kennewick", "kenosha", "killeen", "kissimmee", "knoxville", "lacey", "lafayette", "lake charles", "lakeland",
    "lakewood", "lancaster", "lansing", "laredo", "las cruces", "las vegas", "layton", "leominster", "lewisville",
    "lexington", "lincoln", "little rock", "long beach", "lorain", "los angeles", "louisville", "lowell", "lubbock",
    "macon", "madison", "manchester", "marina", "marysville", "mcallen", "mchenry", "medford", "melbourne",
    "memphis", "merced", "mesa", "mesquite", "miami", "milwaukee", "minneapolis", "miramar", "mission viejo",
    "mobile", "modesto", "monroe", "monterey", "montgomery", "moreno valley", "murfreesboro", "murrieta",
    "muskegon", "myrtle beach", "naperville", "naples", "nashua", "nashville", "new bedford", "new haven",
    "new london", "new orleans", "new york", "new york city", "newark", "newburgh", "newport news", "norfolk",
    "normal", "norman", "north charleston", "north las vegas", "north port", "norwalk", "norwich", "oakland",
    "ocala", "oceanside", "odessa", "ogden", "oklahoma city", "olathe", "olympia", "omaha", "ontario", "orange",
    "orem", "orlando", "overland park", "oxnard", "palm bay", "palm springs", "palmdale", "panama city",
    "pasadena", "paterson", "pembroke pines", "pensacola", "peoria", "philadelphia", "phoenix", "pittsburgh",
    "plano", "pomona", "pompano beach", "port arthur", "port orange", "port saint lucie", "port st. lucie",
    "portland", "portsmouth", "poughkeepsie", "providence", "provo", "pueblo", "punta gorda", "racine", "raleigh",
    "rancho cucamonga", "reading", "redding", "reno", "richland", "richmond", "richmond county", "riverside",
    "roanoke", "rochester", "rockford", "roseville", "round lake beach", "sacramento", "saginaw", "saint louis",
    "saint paul", "saint petersburg", "salem", "salinas", "salt lake city", "san antonio", "san bernardino",
    "san buenaventura", "san diego", "san francisco", "san jose", "santa ana", "santa barbara", "santa clara",
    "santa clarita", "santa cruz", "santa maria", "santa rosa", "sarasota", "savannah", "scottsdale", "scranton",
    "seaside", "seattle", "sebastian", "shreveport", "simi valley", "sioux city", "sioux falls", "south bend",
    "south lyon", "spartanburg", "spokane", "springdale", "springfield", "st. louis", "st. paul", "st. petersburg",
    "stamford", "sterling heights", "stockton", "sunnyvale", "syracuse", "tacoma", "tallahassee", "tampa",
    "temecula", "tempe", "thornton", "thousand oaks", "toledo", "topeka", "torrance", "trenton", "tucson",
    "tulsa", "tuscaloosa", "tyler", "utica", "vallejo", "vancouver", "vero beach", "victorville", "virginia beach",
    "visalia", "waco", "warren", "washington", "waterbury", "waterloo", "west covina", "west valley city",
    "westminster", "wichita", "wilmington", "winston", "winter haven", "worcester", "yakima", "yonkers", "york",
    "youngstown"
}

# Conversation patterns and responses
GREETING_PATTERNS = [
    r'h[ei](?:llo)?|hey|hi there|howdy|sup|good (morning|afternoon|evening)',
    r'how are you',
]

MOOD_PATTERNS = {
    'bored': r'(?:i\'?m\s)?bored|nothing to do',
    'excited': r'(?:i\'?m\s)?excited|can\'?t wait|looking forward',
    'tired': r'(?:i\'?m\s)?tired|exhausted|sleepy',
    'happy': r'(?:i\'?m\s)?happy|glad|feeling good',
    'sad': r'(?:i\'?m\s)?sad|down|upset'
}

INTEREST_PATTERNS = {
    'music': r'music|concert|band|singing|performance',
    'sports': r'sports?|game|match|tournament',
    'arts': r'art|museum|gallery|exhibition|theater|theatre',
    'food': r'food|restaurant|dining|cuisine|eat',
    'outdoor': r'outdoor|nature|park|hiking|walking'
}

EVENT_PATTERNS = [
    r'what\'?s? (?:is )?happening',
    r'any events',
    r'show me',
    r'looking for',
    r'want to (?:go|see|do)',
    r'are there any',
    # Interest-based patterns
    r'interested in (?:art|music|sports|food|shows|concerts|events|restaurants|bands|festivals|performances|dining)',
    r'like (?:art|music|sports|food|shows|concerts|events|restaurants|bands|festivals|performances|dining)',
    r'love (?:art|music|sports|food|shows|concerts|events|restaurants|bands|festivals|performances|dining)',
    r'enjoy (?:art|music|sports|food|shows|concerts|events|restaurants|bands|festivals|performances|dining)',
    # Event discovery patterns
    r'find .* (?:events|shows|concerts|restaurants|performances)',
    r'see .* (?:events|shows|concerts|restaurants|performances)',
    # Category-specific patterns
    r'(?:art|music|sports|food|shows|concerts|restaurants|bands|festivals|performances) .* near',
    r'(?:art|music|sports|food|shows|concerts|restaurants|bands|festivals|performances) .* in',
    # Food specific patterns
    r'(?:food|restaurants|dining|eat|hungry) .* (?:near|in|around)',
    r'places to eat',
    r'good restaurants',
    # Music specific patterns
    r'(?:bands?|concerts?|music|shows?|performances?) .* (?:near|in|around)',
    r'live music',
    r'who\'?s? (?:playing|performing)',
    r'music venues?'
]

def contains_event_keywords(text: str) -> bool:
    """Check if the message contains any event-related keywords."""
    text_lower = text.lower()
    
    # Expanded interest words and verbs
    interest_words = {
        'art', 'music', 'sports', 'food', 'shows', 'concerts', 'events', 'activities',
        'restaurant', 'restaurants', 'dining', 'band', 'bands', 'festival', 'festivals',
        'performance', 'performances', 'venue', 'venues', 'gallery', 'galleries',
        'museum', 'museums', 'theater', 'theatre', 'food', 'dining', 'cuisine',
        'entertainment', 'nightlife', 'bar', 'bars', 'club', 'clubs'
    }
    
    interest_verbs = {
        'like', 'love', 'enjoy', 'interested', 'want', 'looking', 'seeking',
        'searching', 'find', 'discover', 'explore', 'check', 'see', 'visit',
        'try', 'experience', 'attend', 'go'
    }
    
    # Food-specific phrases
    food_phrases = {
        'places to eat', 'good food', 'restaurants', 'dining', 'hungry',
        'food scene', 'best restaurants', 'local food', 'cuisine'
    }
    
    # Music-specific phrases
    music_phrases = {
        'live music', 'concerts', 'bands', 'shows', 'performances', 'gigs',
        'music venue', 'playing tonight', 'performing', 'music scene'
    }
    
    words = set(text_lower.split())
    
    # Check for direct interest expressions
    if (words & interest_verbs) and (words & interest_words):
        return True
    
    # Check for food-specific phrases
    if any(phrase in text_lower for phrase in food_phrases):
        return True
        
    # Check for music-specific phrases
    if any(phrase in text_lower for phrase in music_phrases):
        return True
        
    # Consider short affirmative responses as event-related if they're the main content
    if len(text_lower.split()) <= 3 and any(word in text_lower for word in {'yes', 'yeah', 'sure', 'ok', 'okay', 'fine', 'please'}):
        return True
        
    return any(keyword in text_lower for keyword in EVENT_KEYWORDS)

def extract_location(text: str) -> str:
    """Extract location from message or return None."""
    # Skip location extraction if the message is just about time
    time_only_patterns = [
        r'^(tonight|today|tomorrow|this weekend|next week|in \w+)$',
        r'^what about (tonight|today|tomorrow|this weekend|next week|in \w+)\??$',
        r'^show me (tonight|today|tomorrow|this weekend|next week|in \w+)\??$',
        r'^(january|february|march|april|may|june|july|august|september|october|november|december)\??$',
        r'^in (january|february|march|april|may|june|july|august|september|october|november|december)\??$',
        r'^what about (january|february|march|april|may|june|july|august|september|october|november|december)\??$',
        r'^what about later in (january|february|march|april|may|june|july|august|september|october|november|december)\??$'
    ]
    
    for pattern in time_only_patterns:
        if re.match(pattern, text.lower().strip()):
            return None
    
    # First try to find exact city matches
    text_lower = text.lower()
    for city in ALLOWED_CITIES:
        # Check for exact city mentions with word boundaries
        if re.search(rf'\b{re.escape(city)}\b', text_lower):
            return city.title()
    
    # If no exact match found, try the common location patterns but verify against allowed cities
    location_patterns = [
        r'in ([A-Za-z\s,]+?)(?:\s(?:tonight|today|tomorrow|this weekend|next week|this summer|in \w+)|[.!?]|$)',
        r'near ([A-Za-z\s,]+?)(?:\s(?:tonight|today|tomorrow|this weekend|next week|this summer|in \w+)|[.!?]|$)',
        r'around ([A-Za-z\s,]+?)(?:\s(?:tonight|today|tomorrow|this weekend|next week|this summer|in \w+)|[.!?]|$)',
        r'at ([A-Za-z\s,]+?)(?:\s(?:tonight|today|tomorrow|this weekend|next week|this summer|in \w+)|[.!?]|$)',
        r'for ([A-Za-z\s,]+?)(?:\s(?:tonight|today|tomorrow|this weekend|next week|this summer|in \w+)|[.!?]|$)',
        r'(?:^|\s)([A-Za-z\s,]+?)(?:\s(?:events|things|activities|concerts|shows))',
        r'(?:going to|visiting) ([A-Za-z\s,]+)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text_lower)
        if match:
            location = match.group(1).strip()
            # Check if the extracted location matches any allowed city
            for city in ALLOWED_CITIES:
                if city in location.lower():
                    return city.title()
    
    return None

def parse_date_info(text: str) -> Tuple[datetime, datetime]:
    """Extract date range from user input."""
    text = text.lower()
    today = datetime.now()
    
    # Handle "this weekend"
    if 'weekend' in text:
        # Calculate the next weekend
        days_ahead = 5 - today.weekday()  # Friday
        if days_ahead <= 0:  # If it's already weekend
            days_ahead += 7
        start_date = today + timedelta(days=days_ahead)
        end_date = start_date + timedelta(days=2)  # Include Sunday
        return start_date, end_date

    # Handle "today"
    if 'today' in text:
        return today, today + timedelta(days=1)

    # Handle "tomorrow"
    if 'tomorrow' in text:
        tomorrow = today + timedelta(days=1)
        return tomorrow, tomorrow + timedelta(days=1)

    # Handle "next week"
    if 'next week' in text:
        start_date = today + timedelta(days=7)
        return start_date, start_date + timedelta(days=7)

    # Handle "this month"
    if 'this month' in text:
        return today, today.replace(day=1) + timedelta(days=32)

    # Default to next 30 days
    return today, today + timedelta(days=30)

def get_mock_events_for_city(location: str, location_data: Any, start_date: datetime) -> List[Dict[Any, Any]]:
    """Generate high-quality mock events specific to a city."""
    events = []
    
    # Enhanced city-specific events with more realistic details
    city_specific_events = {
        "seattle": [
            {
                "name": "Bumbershoot Music & Arts Festival",
                "venue": "Seattle Center",
                "category": "Music & Arts Festival",
                "description": "Seattle's premier music and arts festival featuring local and international artists, interactive art installations, and diverse food vendors.",
                "price": "$85 - $165"
            },
            {
                "name": "Live at The Crocodile: Indie Rock Night",
                "venue": "The Crocodile",
                "category": "Live Music",
                "description": "Seattle's best indie bands perform live at the historic Crocodile venue. Features emerging local talent and established acts.",
                "price": "$25 - $40"
            },
            {
                "name": "Pike Place Market Food Tour",
                "venue": "Pike Place Market",
                "category": "Food & Drink",
                "description": "Guided culinary tour through Seattle's famous Pike Place Market. Sample local delicacies and meet local vendors.",
                "price": "$45 - $75"
            },
            {
                "name": "Climate Pledge Arena Concert Series",
                "venue": "Climate Pledge Arena",
                "category": "Concert",
                "description": "Major touring artists perform at Seattle's premier arena venue. State-of-the-art sound and production.",
                "price": "$75 - $250"
            },
            {
                "name": "Green Lake Summer Festival",
                "venue": "Green Lake Park",
                "category": "Community Festival",
                "description": "Family-friendly community festival with live music, local food vendors, activities, and water sports demonstrations.",
                "price": "$0 - $10"
            }
        ],
        "chicago": [
            {
                "name": "Lollapalooza After Shows",
                "venue": "House of Blues Chicago",
                "category": "Music Festival",
                "description": "Official after-show performances featuring Lollapalooza artists in an intimate setting.",
                "price": "$45 - $85"
            },
            {
                "name": "Taste of Chicago",
                "venue": "Grant Park",
                "category": "Food Festival",
                "description": "Chicago's largest food festival featuring local restaurants, live music, and cooking demonstrations.",
                "price": "Free entry, food tickets available"
            },
            {
                "name": "Blues on the Lake",
                "venue": "Navy Pier",
                "category": "Live Music",
                "description": "Evening of Chicago Blues music with stunning lakefront views. Features local blues legends.",
                "price": "$35 - $65"
            },
            {
                "name": "Wrigleyville Summer Bash",
                "venue": "Wrigley Field",
                "category": "Community Festival",
                "description": "Neighborhood celebration with Cubs theme, local vendors, and family activities.",
                "price": "$10 - $25"
            },
            {
                "name": "Art Institute After Dark",
                "venue": "Art Institute of Chicago",
                "category": "Arts & Culture",
                "description": "Special evening access to exhibitions with live music, cocktails, and interactive art activities.",
                "price": "$30 - $45"
            }
        ],
        "new york": [
            {
                "name": "Summer Stage in Central Park",
                "venue": "Central Park",
                "category": "Concert Series",
                "description": "Free outdoor concerts featuring diverse musical acts in the heart of Central Park.",
                "price": "Free - $50 VIP"
            },
            {
                "name": "Broadway in Bryant Park",
                "venue": "Bryant Park",
                "category": "Theater",
                "description": "Lunchtime performances featuring cast members from current Broadway shows.",
                "price": "Free"
            },
            {
                "name": "MSG Concert Series",
                "venue": "Madison Square Garden",
                "category": "Concert",
                "description": "World-class artists perform at The World's Most Famous Arena.",
                "price": "$85 - $350"
            },
            {
                "name": "Times Square Street Food Festival",
                "venue": "Times Square",
                "category": "Food & Drink",
                "description": "International street food festival featuring NYC's best food trucks and vendors.",
                "price": "$5 - $25 per item"
            },
            {
                "name": "Met Rooftop Bar & Art Installation",
                "venue": "Metropolitan Museum of Art",
                "category": "Arts & Culture",
                "description": "Enjoy drinks and contemporary art installations with stunning Central Park views.",
                "price": "$25 - $45"
            }
        ]
    }
    
    # Default events template for other cities
    default_events = [
        {
            "name": f"{location} Summer Music Festival",
            "venue": f"{location} City Park",
            "category": "Music Festival",
            "description": f"Annual music festival featuring local and regional artists in {location}.",
            "price": "$25 - $45"
        },
        {
            "name": f"Food Truck Friday",
            "venue": f"{location} Downtown",
            "category": "Food & Drink",
            "description": "Weekly gathering of the city's best food trucks with live music and local vendors.",
            "price": "Free entry, food prices vary"
        },
        {
            "name": f"{location} Arts Walk",
            "venue": f"{location} Arts District",
            "category": "Arts & Culture",
            "description": "Monthly art walk featuring local galleries, street performers, and pop-up exhibitions.",
            "price": "Free"
        },
        {
            "name": f"Community Concert Series",
            "venue": f"{location} Amphitheater",
            "category": "Concert",
            "description": "Weekly outdoor concerts featuring diverse musical acts from the local scene.",
            "price": "$15 - $30"
        },
        {
            "name": f"{location} Makers Market",
            "venue": f"{location} Convention Center",
            "category": "Shopping",
            "description": "Local artisans and craftspeople showcase their work with demonstrations and workshops.",
            "price": "$5 - $10"
        }
    ]
    
    # Get the events list for this city or use defaults
    event_list = city_specific_events.get(location.lower(), default_events)
    
    # Generate events with proper dates and coordinates
    for i, event in enumerate(event_list):
        if isinstance(event, dict):
            event_data = event.copy()
        else:
            # Handle old tuple format if it exists
            venue, name, category, desc = event
            event_data = {
                "name": name,
                "venue": venue,
                "category": category,
                "description": desc,
                "price": "$" + str(15 + (i * 10))
            }
            
        # Add common fields
        event_data.update({
            "location": event_data["venue"],
            "date": (start_date + timedelta(days=i+1)).strftime("%Y-%m-%d"),
            "url": f"https://www.eventbrite.com/d/{location.lower()}/{event_data['category'].lower()}/",
            "coordinates": (location_data.latitude, location_data.longitude) if location_data else (0, 0)
        })
        events.append(event_data)
    
    return events

def extract_search_parameters(text: str) -> Dict[str, Any]:
    """Extract additional search parameters from user input."""
    params = {
        "classificationName": None,
        "genreName": None,
        "familyFriendly": None,
        "keyword": None
    }
    
    text_lower = text.lower()
    
    # Expanded classifications/categories
    categories = {
        "music": ["music", "concert", "concerts", "band", "singer", "musical", "gig", "performance", "live music"],
        "sports": ["sports", "sport", "game", "match", "tournament", "competition", "athletic", "racing", "marathon"],
        "arts": ["art", "arts", "theatre", "theater", "dance", "ballet", "opera", "gallery", "exhibition", "museum", "painting", "sculpture"],
        "family": ["family", "kids", "children", "child", "parent", "toddler", "baby", "teen", "youth"],
        "comedy": ["comedy", "comedian", "stand-up", "standup", "improv", "funny", "humor"],
        "film": ["film", "movie", "cinema", "screening", "premiere", "documentary"],
        "food": ["food", "dining", "culinary", "cooking", "tasting", "wine", "beer", "festival", "restaurant", "chef"],
        "educational": ["learning", "workshop", "seminar", "class", "course", "lecture", "training", "education"],
        "business": ["networking", "conference", "meetup", "professional", "business", "entrepreneur", "startup"],
        "community": ["community", "neighborhood", "local", "charity", "volunteer", "social", "meetup"],
        "outdoor": ["outdoor", "nature", "hiking", "camping", "adventure", "park", "garden", "beach"],
        "wellness": ["wellness", "health", "fitness", "yoga", "meditation", "mindfulness", "spa"],
        "technology": ["tech", "technology", "digital", "gaming", "esports", "virtual", "computer"],
        "nightlife": ["club", "party", "dance", "DJ", "nightclub", "bar", "pub"],
        "shopping": ["market", "fair", "bazaar", "shopping", "craft", "vintage", "antique", "pop-up"]
    }
    
    # Expanded genres (music and more)
    genres = {
        "rock": ["rock", "alternative", "indie", "punk", "metal", "grunge"],
        "pop": ["pop", "popular", "top 40", "mainstream"],
        "hip-hop-rap": ["hip hop", "rap", "hip-hop", "r&b", "rhythm and blues"],
        "country": ["country", "folk", "americana", "bluegrass"],
        "jazz": ["jazz", "blues", "swing", "bebop", "fusion"],
        "classical": ["classical", "orchestra", "symphony", "chamber", "opera"],
        "electronic": ["electronic", "edm", "techno", "house", "trance", "dubstep"],
        "world": ["world", "international", "global", "ethnic", "traditional"],
        "latin": ["latin", "salsa", "reggaeton", "bachata", "merengue"],
        "reggae": ["reggae", "ska", "dub", "caribbean"],
        "experimental": ["experimental", "avant-garde", "contemporary", "modern"]
    }
    
    # Activity types
    activities = {
        "active": ["sports", "fitness", "exercise", "workout", "training", "competition"],
        "relaxing": ["spa", "wellness", "meditation", "yoga", "relaxation"],
        "social": ["meetup", "social", "gathering", "party", "networking"],
        "learning": ["class", "workshop", "seminar", "course", "training"],
        "entertainment": ["show", "performance", "concert", "movie", "theatre"],
        "outdoor": ["hiking", "camping", "nature", "adventure", "park"],
        "food_drink": ["dining", "tasting", "cooking", "food", "drink"],
        "shopping": ["market", "shopping", "fair", "bazaar"]
    }
    
    # Check categories
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            params["classificationName"] = category
            break
    
    # Check genres
    for genre, keywords in genres.items():
        if any(keyword in text_lower for keyword in keywords):
            params["genreName"] = genre
            break
    
    # Check for family-friendly indicators
    family_keywords = [
        "family friendly", "kid friendly", "children", "family", "all ages",
        "kid", "child", "parent", "toddler", "baby", "teen", "youth"
    ]
    if any(keyword in text_lower for keyword in family_keywords):
        params["familyFriendly"] = "yes"
    
    # Extract specific artist/performer/event names
    artist_indicators = [
        "by", "from", "see", "watch", "featuring", "feat", "with",
        "performing", "presents", "starring", "showcasing"
    ]
    for indicator in artist_indicators:
        if indicator in text_lower:
            parts = text_lower.split(indicator)
            if len(parts) > 1:
                # Take the next word group as potential artist/event name
                name_part = parts[1].strip().split()
                if name_part and not name_part[0] in ["in", "at", "on", "the"]:
                    # Take up to 3 words for the name
                    name = " ".join(name_part[:3])
                    params["keyword"] = name
                    break
    
    return {k: v for k, v in params.items() if v is not None}

def get_events_from_ticketmaster(location: str, radius_km: int = 10, date_range: Tuple[datetime, datetime] = None, search_text: str = "") -> List[Dict[Any, Any]]:
    """Fetch events from Ticketmaster API based on location and date range."""
    try:
        # Get coordinates for the location
        location_data = geolocator.geocode(location)
        if not location_data:
            print(f"Could not geocode location: {location}")
            return get_mock_events_for_city(location, None, datetime.now())

        # Convert radius to miles (Ticketmaster uses miles)
        radius_mi = int(radius_km * 0.621371)

        # Use provided date range or default
        if not date_range:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=90)
        else:
            start_date, end_date = date_range

        # Format dates in ISO format
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Extract additional search parameters
        search_params = extract_search_parameters(search_text)

        # Prepare API request
        params = {
            "apikey": TICKETMASTER_API_KEY,
            "latlong": f"{location_data.latitude},{location_data.longitude}",
            "radius": radius_mi,
            "startDateTime": start_date_str,
            "endDateTime": end_date_str,
            "size": 20,  # Number of events to return
            "sort": "date,asc",
            **search_params  # Add extracted search parameters
        }

        print(f"\n=== Making Ticketmaster API Request ===")
        print(f"URL: {TICKETMASTER_API_URL}")
        print(f"Parameters: {params}")

        response = requests.get(TICKETMASTER_API_URL, params=params)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response from Ticketmaster: {response.text[:500]}")
            return get_mock_events_for_city(location, location_data, start_date)

        events_data = response.json()
        print(f"API Response: {json.dumps(events_data, indent=2)[:500]}...")
        
        # Check if we have any events
        if not events_data.get('_embedded', {}).get('events', []):
            print("No events found in API response")
            return get_mock_events_for_city(location, location_data, start_date)

        events = []
        for event in events_data['_embedded']['events']:
            try:
                # Get venue information
                venue = event.get('_embedded', {}).get('venues', [{}])[0]
                
                # Get price ranges
                price_ranges = event.get('priceRanges', [])
                if price_ranges:
                    min_price = price_ranges[0].get('min', 0)
                    max_price = price_ranges[0].get('max', 0)
                    price = f"${min_price:.2f} - ${max_price:.2f}" if min_price or max_price else "Check website for prices"
                else:
                    price = "Check website for prices"
                
                # Get event description
                description = event.get('description', event.get('info', 'No description available'))
                if len(description) > 200:
                    description = description[:197] + '...'
                
                # Format the event data
                event_data = {
                    "name": event.get('name', 'Unnamed Event'),
                    "description": description,
                    "location": f"{venue.get('name', 'TBA')}, {venue.get('address', {}).get('line1', '')}",
                    "date": datetime.strptime(event['dates']['start']['dateTime'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d"),
                    "url": event.get('url', ''),
                    "coordinates": (
                        float(venue.get('location', {}).get('latitude', location_data.latitude)),
                        float(venue.get('location', {}).get('longitude', location_data.longitude))
                    ),
                    "category": event.get('classifications', [{}])[0].get('segment', {}).get('name', 'General'),
                    "price": price,
                    "image": event.get('images', [{}])[0].get('url') if event.get('images') else None
                }
                events.append(event_data)
                print(f"Successfully processed event: {event_data['name']}")
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                continue

        if not events:
            print("No valid events found, falling back to mock events")
            return get_mock_events_for_city(location, location_data, start_date)

        print(f"Successfully found {len(events)} events")
        return events

    except Exception as e:
        print(f"Error in event fetching: {str(e)}")
        traceback.print_exc()
        return get_mock_events_for_city(location, location_data if 'location_data' in locals() else None, start_date if 'start_date' in locals() else datetime.now())

def get_events_near_location(location: str, date_range: Tuple[datetime, datetime], query: str = "") -> List[Dict[str, Any]]:
    """Search for events near a location using Ticketmaster API."""
    try:
        # Get coordinates for the location
        location_info = geolocator.geocode(location)
        if not location_info:
            print(f"Could not geocode location: {location}")
            return []

        # Prepare API parameters
        params = {
            'apikey': TICKETMASTER_API_KEY,
            'latlong': f"{location_info.latitude},{location_info.longitude}",
            'radius': '50',  # 50-mile radius
            'unit': 'miles',
            'startDateTime': date_range[0].strftime('%Y-%m-%dT%H:%M:%SZ'),
            'endDateTime': date_range[1].strftime('%Y-%m-%dT%H:%M:%SZ'),
            'size': 20  # Number of events to return
        }

        # Add keyword search if query contains specific terms
        query_lower = query.lower()
        if any(term in query_lower for term in ['music', 'concert', 'festival']):
            params['classificationName'] = 'music'
        elif any(term in query_lower for term in ['sports', 'game', 'match']):
            params['classificationName'] = 'sports'
        elif any(term in query_lower for term in ['family', 'kids']):
            params['classificationName'] = 'family'
        elif any(term in query_lower for term in ['art', 'museum', 'theatre', 'theater']):
            params['classificationName'] = 'arts'

        print(f"Making Ticketmaster API request with params: {params}")
        
        # Make API request
        response = requests.get(TICKETMASTER_API_URL, params=params)
        if response.status_code != 200:
            print(f"Error from Ticketmaster API: {response.status_code}")
            return []

        data = response.json()
        if '_embedded' not in data or 'events' not in data['_embedded']:
            print("No events found in API response")
            return []

        events = []
        for event in data['_embedded']['events']:
            try:
                # Extract event details with safe fallbacks
                event_data = {
                    'name': event.get('name', 'Event Name Not Available'),
                    'date': event.get('dates', {}).get('start', {}).get('localDate', 'Date TBA'),
                    'location': event.get('_embedded', {}).get('venues', [{}])[0].get('name', 'Venue TBA'),
                    'url': event.get('url', '#'),  # Fallback to '#' if no URL available
                    'category': event.get('classifications', [{}])[0].get('segment', {}).get('name', 'Event'),
                    'description': event.get('info', event.get('description', 'No description available')),
                    'price': 'Check ticket site for prices'
                }

                # Add price range if available
                if 'priceRanges' in event:
                    price_range = event['priceRanges'][0]
                    if price_range.get('min') == price_range.get('max'):
                        event_data['price'] = f"${price_range['min']:.2f}"
                    else:
                        event_data['price'] = f"${price_range['min']:.2f} - ${price_range['max']:.2f}"

                # Add image if available
                if 'images' in event and event['images']:
                    # Find the best image (prefer 16:9 ratio if available)
                    best_image = None
                    for img in event['images']:
                        if img.get('ratio') == '16_9' and img.get('width', 0) >= 640:
                            best_image = img
                            break
                    if not best_image and event['images']:
                        best_image = event['images'][0]
                    
                    if best_image:
                        event_data['image'] = best_image.get('url')

                events.append(event_data)
                print(f"Successfully processed event: {event_data['name']}")

            except Exception as e:
                print(f"Error processing event: {str(e)}")
                continue

        return events

    except Exception as e:
        print(f"Error fetching events: {str(e)}")
        traceback.print_exc()
        return []

def get_conversation_response(text: str, context: Dict[str, Any] = None) -> str:
    """Generate a conversational response based on user input."""
    try:
        # Use Gemini API instead of local GPT4All
        if 'gemini_model' not in globals() or globals().get('gemini_model') is None:
            print("Gemini model not configured, using template response.")
            return get_template_response(text)

        # Create a system prompt that defines the chatbot's role
        system_prompt = """You are a friendly event chatbot assistant. You help users find events and activities they might enjoy.
        You are knowledgeable about various types of events including concerts, sports, arts, and more.
        Keep your responses friendly, concise, and focused on helping users discover events."""

        # Combine the context with the user's message
        if context and context.get('location'):
            full_prompt = f"{system_prompt}\nUser's location: {context['location']}\nUser: {text}\nAssistant:"
        else:
            full_prompt = f"{system_prompt}\nUser: {text}\nAssistant:"

        print("Generating response with Google Gemini API...")
        # Generate response using Gemini
        response = globals()['gemini_model'].generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=100, # Max tokens for response
            )
        )
        
        # Extract text from the response
        generated_text = response.text.strip()
        print(f"Gemini API response: {generated_text}")

        # If the response is empty or too short, fall back to template responses
        if not generated_text or len(generated_text) < 10:
            print("Gemini response too short, falling back to template")
            return get_template_response(text)
            
        return generated_text

    except Exception as e:
        print(f"Error in conversation response: {str(e)}")
        traceback.print_exc()
        return get_template_response(text)

def get_template_response(text: str) -> str:
    """Fallback function for template-based responses."""
    text_lower = text.lower()
    
    # Check for greetings
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, text_lower):
            return random.choice([
                "Hey there! 😊 How can I help make your day more exciting?",
                "Hi! I'm always happy to chat and help you discover fun things to do!",
                "Hello! Looking for something fun? I know lots of great events and activities!",
                "Hey! Whether you want to find events or just chat, I'm here to help!"
            ])
    
    # Check for moods
    for mood, pattern in MOOD_PATTERNS.items():
        if re.search(pattern, text_lower):
            if mood in MOOD_KEYWORDS:
                return random.choice(MOOD_KEYWORDS[mood])
    
    # Check for interests
    for interest, pattern in INTEREST_PATTERNS.items():
        if re.search(pattern, text_lower):
            if interest in INTEREST_KEYWORDS:
                return random.choice(INTEREST_KEYWORDS[interest])
    
    # Default responses
    return random.choice([
        "I'd love to help you discover something fun! What city should I look in?",
        "Tell me what city you're interested in, and I'll help you find some great events! 🎉",
        "I know lots of exciting events! Which city would you like to explore?",
        "Ready to find something fun to do? Just let me know which city you're interested in! 😊"
    ])

def generate_response(user_input: str, user_location: str = None) -> str:
    """Generate a response based on user input and nearby events."""
    try:
        # First try to extract location from the current message
        message_location = extract_location(user_input)
        
        # Use the most recently mentioned location (from message or previous location)
        location = message_location or user_location
        
        # Check if the message contains event-related keywords
        contains_event_query = any(re.search(pattern, user_input.lower()) for pattern in EVENT_PATTERNS)
        
        if contains_event_query and location:
            # If asking about events and we have a location, show events
            date_range = parse_date_info(user_input)
            print(f"Searching for events in: {location}")
            print(f"Date range: {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}")
            nearby_events = get_events_from_ticketmaster(location, 10, date_range, user_input)
            
            if not nearby_events:
                # If no events found, get AI response explaining why and suggesting alternatives
                context = {'location': location, 'no_events': True}
                return get_conversation_response(user_input, context)
            
            # Create event response HTML
            date_info = ""
            if date_range[0].month == date_range[1].month:
                date_info = f" in {calendar.month_name[date_range[0].month]} {date_range[0].year}"
            elif date_range[1] - date_range[0] <= timedelta(days=2):
                if "weekend" in user_input.lower():
                    date_info = " this weekend"
                else:
                    date_info = f" from {date_range[0].strftime('%B %d')} to {date_range[1].strftime('%B %d')}"
            
            # Get AI response to introduce the events
            intro_context = {'location': location, 'event_count': len(nearby_events)}
            ai_intro = get_conversation_response(f"Introduce these {len(nearby_events)} events in {location}{date_info}", intro_context)
            
            response = [f"<div class='events-response'><p>{ai_intro}</p><h2>Events in {location}{date_info}</h2><div class='events-grid'>"]
            
            for event in nearby_events:
                image_html = f"<img src='{event['image']}' alt='{event['name']}' class='event-image'>" if event.get('image') else ""
                response.append(
                    f"<div class='event-card'>"
                    f"{image_html}"
                    f"<div class='event-content'>"
                    f"<h3>{event['name']}</h3>"
                    f"<div class='event-details'>"
                    f"<p><strong>📅</strong> {event['date']}</p>"
                    f"<p><strong>📍</strong> {event['location']}</p>"
                    f"<p><strong>💰</strong> {event['price']}</p>"
                    f"<p><strong>🏷️</strong> {event['category']}</p>"
                    f"<p>{event['description']}</p>"
                    f"</div>"
                    f"<a href='{event['url']}' target='_blank' class='ticket-button'>Get Tickets →</a>"
                    f"</div>"
                    f"</div>"
                )
            
            response.append("</div></div>")
            return "".join(response)
        else:
            # Handle conversation
            context = {'location': location} if location else None
            return get_conversation_response(user_input, context)

    except Exception as e:
        print(f"Error generating response: {str(e)}")
        traceback.print_exc()
        return "I encountered an error while processing your request. Could you try rephrasing that?"

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chat interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Event Companion</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }
            .chat-container { 
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 10px;
                height: 500px;  /* Increased height */
                overflow-y: auto;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .message { 
                margin: 10px 0;
                padding: 10px 15px;
                border-radius: 15px;
                max-width: 80%;
                word-wrap: break-word;
            }
            .user-message { 
                background-color: #1a73e8;
                color: white;
                margin-left: auto;
            }
            .bot-message { 
                background-color: #e9ecef;
                color: #212529;
            }
            .welcome-message {
                text-align: center;
                margin-bottom: 30px;
                color: #333;
                max-width: 800px;  /* Increased width */
                margin-left: auto;
                margin-right: auto;
                padding: 20px;
            }
            .welcome-message h1 {
                color: #1a73e8;
                margin-bottom: 15px;
                font-size: 2em;
            }
            .welcome-message p {
                font-size: 1.1em;
                line-height: 1.6;
                color: #555;
                margin-bottom: 20px;
            }
            .chat-suggestions {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                margin-top: 20px;
                justify-content: center;
            }
            .suggestion-chip {
                background-color: #e8f0fe;
                color: #1a73e8;
                padding: 10px 20px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 1em;
                transition: all 0.2s ease;
                border: 1px solid #1a73e8;
                user-select: none;
            }
            .suggestion-chip:hover {
                background-color: #1a73e8;
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .input-container { 
                display: flex;
                gap: 15px;
                margin-top: 20px;
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            input { 
                flex-grow: 1;
                padding: 12px 20px;
                border: 2px solid #ddd;
                border-radius: 25px;
                font-size: 16px;
                transition: border-color 0.2s;
            }
            input:focus {
                outline: none;
                border-color: #1a73e8;
            }
            button { 
                padding: 12px 25px;
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: all 0.2s;
            }
            button:hover { 
                background-color: #1557b0;
                transform: translateY(-2px);
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .events-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .event-card {
                border: 1px solid #ddd;
                border-radius: 12px;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
                overflow: hidden;
                height: 400px;
                display: flex;
                flex-direction: column;
            }
            .event-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }
            .event-image {
                width: 100%;
                height: 150px;
                object-fit: cover;
                border-bottom: 1px solid #eee;
            }
            .event-content {
                padding: 15px;
                flex-grow: 1;
                display: flex;
                flex-direction: column;
            }
            .event-card h3 {
                margin: 0 0 10px 0;
                color: #1a73e8;
                font-size: 1.1em;
                line-height: 1.3;
            }
            .event-details {
                font-size: 13px;
                line-height: 1.4;
                flex-grow: 1;
                overflow-y: auto;
            }
            .event-details p {
                margin: 5px 0;
            }
            .ticket-button {
                display: block;
                margin-top: 10px;
                padding: 8px 15px;
                background-color: #1a73e8;
                color: white;
                text-decoration: none;
                border-radius: 20px;
                font-weight: bold;
                transition: background-color 0.2s;
                text-align: center;
            }
            .ticket-button:hover {
                background-color: #1557b0;
                text-decoration: none;
            }
            .filters-container {
                display: none;  /* Hide filters initially */
            }
            .chat-suggestions {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 15px;
                justify-content: center;
            }
            .suggestion-chip {
                background-color: #e8f0fe;
                color: #1a73e8;
                padding: 8px 15px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .suggestion-chip:hover {
                background-color: #d2e3fc;
            }
        </style>
    </head>
    <body>
        <div class="welcome-message">
            <h1>Hi there! 👋</h1>
            <p>I'm your friendly event companion! Whether you're looking for something specific or just want to chat about what's happening around town, I'm here to help. Feel free to start with a simple hello!</p>
            <div class="chat-suggestions">
                <div class="suggestion-chip" data-text="Hi! How are you?">👋 Say Hello</div>
                <div class="suggestion-chip" data-text="I am feeling bored">😕 Feeling Bored</div>
                <div class="suggestion-chip" data-text="What fun things are there to do?">🎉 Find Fun Activities</div>
                <div class="suggestion-chip" data-text="I love music!">🎵 Talk About Music</div>
            </div>
        </div>
        
        <div class="chat-container" id="chat-container">
            <div class="message bot-message">
                Hi! I'm your event finding assistant. You can ask me anything about events, or we can just chat about what interests you. How are you doing today?
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="message" placeholder="Type your message here... (e.g., 'How are you?' or 'What's happening in New York?')" />
            <button id="send-button">Send</button>
        </div>
        
        <script>
            let userLocation = '';
            
            function sendSuggestion(text) {
                if (!text) return;
                const messageInput = document.getElementById('message');
                messageInput.value = text;
                sendMessage();
            }
            
            async function sendMessage() {
                const messageInput = document.getElementById('message');
                const chatContainer = document.getElementById('chat-container');
                
                const message = messageInput.value.trim();
                if (!message) return;
                
                // Add user message to chat
                const userMessageDiv = document.createElement('div');
                userMessageDiv.className = 'message user-message';
                userMessageDiv.textContent = message;
                chatContainer.appendChild(userMessageDiv);
                
                messageInput.value = '';
                
                try {
                    // Send to backend with current location
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: `message=${encodeURIComponent(message)}&location=${encodeURIComponent(userLocation)}`
                    });
                    
                    const data = await response.text();
                    
                    if (!response.ok) {
                        throw new Error(data || 'Failed to get response');
                    }
                    
                    // Add bot response to chat
                    const botMessageDiv = document.createElement('div');
                    botMessageDiv.className = 'message bot-message';
                    botMessageDiv.innerHTML = data;
                    chatContainer.appendChild(botMessageDiv);
                    
                    // Update location if a new one was found in the message
                    const locationMatch = message.match(/in ([A-Za-z\s,]+?)(?:\s|$)/i);
                    if (locationMatch) {
                        userLocation = locationMatch[1].trim();
                    }
                    
                } catch (error) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'message bot-message';
                    errorDiv.textContent = 'Sorry, I encountered an error. Please try again.';
                    chatContainer.appendChild(errorDiv);
                }
                
                // Scroll to bottom
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            // Set up event listeners when the DOM is loaded
            document.addEventListener('DOMContentLoaded', function() {
                // Add click listeners to suggestion chips
                const chips = document.querySelectorAll('.suggestion-chip');
                chips.forEach(chip => {
                    chip.addEventListener('click', function() {
                        const text = this.getAttribute('data-text');
                        if (text) {
                            sendSuggestion(text);
                        }
                    });
                });

                // Add click listener to send button
                document.getElementById('send-button').addEventListener('click', sendMessage);

                // Add enter key listener to input field
                document.getElementById('message').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendMessage();
                    }
                });
            });
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(message: str = Form(...), location: str = Form(default="")):
    """Handle chat messages."""
    try:
        print(f"Processing request - Location: {location}, Message: {message}")
        
        # First check if this is a time-only query
        time_only_patterns = [
            r'^(tonight|today|tomorrow|this weekend|next week|in \w+)$',
            r'^what about (tonight|today|tomorrow|this weekend|next week|in \w+)\??$',
            r'^show me (tonight|today|tomorrow|this weekend|next week|in \w+)\??$',
            r'^(january|february|march|april|may|june|july|august|september|october|november|december)\??$',
            r'^in (january|february|march|april|may|june|july|august|september|october|november|december)\??$',
            r'^what about (january|february|march|april|may|june|july|august|september|october|november|december)\??$',
            r'^what about later in (january|february|march|april|may|june|july|august|september|october|november|december)\??$'
        ]
        
        is_time_only_query = any(re.match(pattern, message.lower().strip()) for pattern in time_only_patterns)
        
        # If it's a time-only query and we have a previous location, use that
        if is_time_only_query and location:
            response = generate_response(message, location)
        else:
            # Try to extract a new location
            new_location = extract_location(message)
            
            # Only update location if we found a valid city
            if new_location:
                location = new_location
            
            response = generate_response(message, location if location else None)
        
        return response

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        traceback.print_exc()
        return "I encountered an error. Could you try rephrasing your message?"

if __name__ == "__main__":
    import uvicorn
    # Render provides the PORT environment variable
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8081)))

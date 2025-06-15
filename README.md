# Event Chatbot

A friendly chatbot that helps users discover events near their location and encourages them to get out of the house. It uses the Ticketmaster API to find real events in your area.

## Features
- Natural language conversation
- Real-time event data from Ticketmaster
- Location-aware event search
- Smart date parsing
- Beautiful, responsive UI
- Event suggestions based on interests
- Rich event details with images and ticket links

## Requirements
- Python 3.8+
- FastAPI
- Uvicorn
- Other dependencies listed in requirements.txt

## Setup

1. Clone the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Ticketmaster API access:
- Create an account on [Ticketmaster Developer Portal](https://developer.ticketmaster.com)
- Get your API key
- Create a `.env` file in the project root with:
```
TICKETMASTER_API_KEY=your_api_key_here
```

4. Run the application:
```bash
python main.py
```

5. Open http://127.0.0.1:8080 in your browser

## Usage

1. Start with a greeting or jump right into asking about events
2. Mention a city name when asking about events
3. Use natural language to specify:
   - Event types (concerts, sports, theater, etc.)
   - Time frame (today, this weekend, next week, etc.)
   - Preferences (music genres, price ranges, etc.)
4. Click on event cards to view full details and get tickets
5. Use the suggestion chips for quick interactions

## Features
- Smart location detection
- Natural date parsing
- Event categorization
- Price information
- Venue details
- Real-time event data from Ticketmaster
- Interactive UI with event cards
- Responsive design for all devices

## Error Handling

The application includes error handling for:
- Invalid locations
- API failures
- Missing API keys
- Network issues
- Invalid user input

## Future Improvements

Potential enhancements for the future:
- Category-based filtering
- Date range selection
- Price range filtering
- Saved favorite locations
- Event reminders
- Social sharing features

## Note

The current version uses a mock events database. In a production environment, you would want to:
- Integrate with a real events API
- Add user authentication
- Implement proper error handling
- Add more sophisticated event filtering
- Cache frequent location queries 
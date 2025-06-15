from typing import List, Dict
import requests

def get_events_from_ticketmaster(location: str, limit: int, date_range: tuple, query: str = None) -> List[Dict]:
    """Get events from Ticketmaster API."""
    try:
        start_date = date_range[0].strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date = date_range[1].strftime("%Y-%m-%dT%H:%M:%SZ")
        
        params = {
            "apikey": TICKETMASTER_API_KEY,
            "city": location,
            "startDateTime": start_date,
            "endDateTime": end_date,
            "size": limit,
            "sort": "date,asc"
        }
        
        if query:
            # Extract keywords for search
            keywords = [word.lower() for word in query.split() 
                       if word.lower() not in STOP_WORDS and len(word) > 2]
            if keywords:
                params["keyword"] = " ".join(keywords)

        response = requests.get(TICKETMASTER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "_embedded" not in data or "events" not in data["_embedded"]:
            print(f"No events found for {location}")
            return []

        events = []
        for event in data["_embedded"]["events"]:
            try:
                # Get the best available image
                images = event.get("images", [])
                image_url = next((img["url"] for img in images 
                                if img.get("ratio") == "16_9" and img.get("width") > 500), 
                               images[0]["url"] if images else None)

                # Get price range
                if "priceRanges" in event:
                    min_price = event["priceRanges"][0].get("min")
                    max_price = event["priceRanges"][0].get("max")
                    currency = event["priceRanges"][0].get("currency", "USD")
                    if min_price == max_price:
                        price = f"${min_price:.2f}"
                    else:
                        price = f"${min_price:.2f} - ${max_price:.2f}"
                else:
                    price = "Price information unavailable"

                # Get venue details
                venue = event["_embedded"]["venues"][0]
                venue_name = venue.get("name", "Venue TBA")
                
                # Get date and time
                local_date = event.get("dates", {}).get("start", {}).get("localDate", "Date TBA")
                local_time = event.get("dates", {}).get("start", {}).get("localTime", "")
                if local_time:
                    date_str = f"{local_date} at {local_time}"
                else:
                    date_str = local_date

                # Get category/genre
                classifications = event.get("classifications", [{}])[0]
                segment = classifications.get("segment", {}).get("name", "")
                genre = classifications.get("genre", {}).get("name", "")
                category = f"{segment} - {genre}" if segment and genre else (segment or genre or "General")

                # Create event dictionary
                event_dict = {
                    "name": event["name"],
                    "date": date_str,
                    "location": f"{venue_name}, {venue.get('city', {}).get('name', '')}", 
                    "price": price,
                    "url": event.get("url", "#"),
                    "image": image_url,
                    "category": category,
                    "description": event.get("description", "").strip() or event.get("info", "").strip() or f"Join us for {event['name']}!"
                }
                events.append(event_dict)
                
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                continue

        return events

    except requests.exceptions.RequestException as e:
        print(f"Error fetching events from Ticketmaster: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return [] 
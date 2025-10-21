import requests
from bs4 import BeautifulSoup
import pandas as pd
import pyttsx3 # Just for fun, let's make it talk!
import re

# --- Setup ---
# Initialize the Text-to-Speech (TTS) engine
engine = pyttsx3.init()

def speak(text):
    """Prints text to the console and speaks it aloud."""
    print(f"🗣️ {text}")
    # Don't speak if the engine isn't ready or if we're on a headless server
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        # Pass silently if TTS fails, no need to crash the script
        pass

# Wikipedia URL for the list of countries by military personnel
url = "https://en.wikipedia.org/wiki/List_of_countries_by_number_of_military_and_paramilitary_personnel"
speak("Starting data fetch from Wikipedia...")

# --- Data Acquisition ---
try:
    # Use a standard header to avoid being blocked, though Wikipedia is usually fine
    headers = {'User-Agent': 'Custom Data Scraper v1.0'}
    res = requests.get(url, headers=headers)
    res.raise_for_status() # Check for bad status codes (4xx or 5xx)
except requests.exceptions.RequestException as e:
    speak(f"FATAL ERROR: Could not connect to Wikipedia. Details: {e}")
    exit(1) # Exit with a non-zero status code to signal an error

soup = BeautifulSoup(res.text, 'html.parser')

# The main data is usually in the first 'wikitable'
# Note: Inspecting the page confirmed the table uses the 'wikitable' class.
table = soup.find("table", class_="wikitable")

if not table:
    speak("ERROR: Could not find the expected data table on the Wikipedia page.")
    exit(1)

# --- Parsing Logic ---
# Extract headers from the first row (<thead> or <tr>)
try:
    # Grab the first row's <th> elements
    headers = [th.text.strip() for th in table.find_all("tr")[0].find_all("th")]
except IndexError:
    speak("ERROR: Table appears empty or headers could not be read.")
    exit(1)

# Extract subsequent rows
rows = []
# Skip the header row (starting from index 1)
for row in table.find_all("tr")[1:]:
    # Handle both <td> (data cells) and <th> (potential sub-headers/country names)
    cols = row.find_all(["td", "th"])
    cols = [col.text.strip() for col in cols]

    # Ensure the row has at least as many columns as the headers to avoid errors
    if len(cols) >= len(headers):
        # Truncate to the exact number of headers just in case of merged columns
        rows.append(cols[:len(headers)])

# --- Data Processing and Output ---
# Create a Pandas DataFrame for easy manipulation
df = pd.DataFrame(rows, columns=headers)

print("\n" + "="*40)
print("👉 Successfully Scraped Data Columns:")
for i, col in enumerate(df.columns):
    print(f"  {i+1}. '{col}'")
print("="*40 + "\n")

# Save the raw data for archival or later analysis
try:
    df.to_csv("military_personnel_data.csv", index=False)
    df.to_excel("military_personnel_data.xlsx", index=False)
    speak("Data successfully structured and saved as CSV and Excel files.")
except Exception as e:
    speak(f"WARNING: Could not save files. Details: {e}")


# --- Interactive Search ---
# The first column is almost certainly the 'Country' name
name_col = df.columns[0]
speak(f"Starting interactive search. Searching on the column: '{name_col}'.")

while True:
    search = input("\n🔍 Enter country name to search (or type 'exit' to quit): ").strip()

    if search.lower() == 'exit':
        speak("Session terminated. Goodbye!")
        break

    if not search:
        speak("Please enter a country name to search.")
        continue

    # Use regex for flexible, partial, case-insensitive searching
    # re.escape makes sure characters like '$' or '(' don't break the pattern
    pattern = re.escape(search.lower())
    
    # Filter the DataFrame: convert search column to lowercase and check for containment
    result = df[df[name_col].str.lower().str.contains(pattern, na=False)]

    if not result.empty:
        # Display the first few matches for the user to see
        print("\n--- Top Matching Results ---")
        print(result.head().to_string(index=False))
        print("-" * 30)

        # Speak the full details of the BEST match (the first one)
        row = result.iloc[0]
        
        # Build a list of formatted strings for TTS
        country_info = [f"{col}: {row[col]}" for col in df.columns]

        speak(f"Found information for {row[name_col]}.")
        for item in country_info[1:]:
             # A slight delay here might make the spoken output clearer, but pyttsx3 handles queuing
             speak(item)

        speak(f"Search complete. {len(result)} total result(s) found for '{search}'.")
    else:
        speak(f"No matching record found for '{search}'. Try a shorter, more general name.")
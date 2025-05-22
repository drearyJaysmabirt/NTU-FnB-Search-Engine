import pygame  # Used for graphical user input (selecting location on NTU map)
import time  # Used to pause UI after selection
import pandas as pd  # Used for handling Excel file data
import pathlib  # Used to handle file paths dynamically across different OS
import openpyxl  # Required to read .xlsx files with pandas
import re  # Import regex module for advanced string splitting
import difflib  # Used for fuzzy string matching

# Load dataset file path dynamically
DATA_FILE = str(pathlib.Path(__file__).parent.resolve()) + "/canteens.xlsx"
image_path = str(pathlib.Path(__file__).parent.resolve()) + "/images/NTUcampus.jpg"
pin_path = str(pathlib.Path(__file__).parent.resolve()) + "/images/pin.png"

# Define ANSI escape sequences for colored console output
PURPLE = "\033[95m"  # Purple (for start & end messages)
BLUE = "\033[94m"  # Light blue (for user input prompts)
RESET = "\033[0m"  # Reset color


def parse_keywords(user_input): #Parses a user input string to handle AND/OR logic with flexible spacing. Single spaces are treated as 'AND' unless part of known multi-word keywords (e.g., 'mixed rice').

    user_input = user_input.lower().strip()

    # List of protected multi-word keywords
    protected_keywords = ['mixed rice']
    placeholder_map = {}

    # Step 1: Temporarily replace protected multi-word keywords with placeholders
    for i, keyword in enumerate(protected_keywords):
        placeholder = f"__kw{i}__"
        user_input = user_input.replace(keyword, placeholder)
        placeholder_map[placeholder] = keyword

    # Step 2: Normalize "and"/"or" spacing (adds spaces around them if missing)
    user_input = re.sub(r'(?<!\s)(and|or)(?!\s)', r' \1 ', user_input)

    # Step 3: Replace remaining multiple spaces with ' and ' (unless already part of 'and'/'or')
    user_input = re.sub(r'\s+', ' ', user_input)  # Collapse all whitespace to single space
    tokens = user_input.split()

    # Step 4: Insert 'and' between tokens that are not 'and' or 'or'
    processed_tokens = []
    for i, token in enumerate(tokens):
        processed_tokens.append(token)
        if i < len(tokens) - 1:
            next_token = tokens[i + 1]
            if token not in ('and', 'or') and next_token not in ('and', 'or'):
                processed_tokens.append('and')  # Insert 'and' between adjacent keywords

    # Step 5: Join and restore protected keywords
    rebuilt_input = ' '.join(processed_tokens)
    for placeholder, original_keyword in placeholder_map.items():
        rebuilt_input = rebuilt_input.replace(placeholder, original_keyword)

    # Step 6: Apply final parsing logic using original OR → AND structure
    parsed_terms = {"OR": []}
    or_groups = re.split(r'\s+or\s+', rebuilt_input)

    for group in or_groups:
        and_terms = re.split(r'\s+and\s+', group.strip())
        parsed_terms["OR"].append(and_terms)

    return parsed_terms



# Function to load all canteen data (keywords, prices, locations)
def load_canteen_data(data_location): # Reads food stall keywords, prices, and locations from the Excel file.

    df_canteen = pd.read_excel(data_location, engine='openpyxl')  # Renamed variable
    keywords, prices, locations = {}, {}, {}      # Initialize dictionaries

    for _, row in df_canteen.iterrows():  # Iterate through dataset rows to extract canteen, stall, keywords, price, and location
        canteen = row['Canteen']
        stall = row['Stall']
        keyword = row['Keywords'].lower()
        price = row['Price']

        try:   # Convert location from string to a tuple of integers (x, y)
            location = list(map(int, row['Location'].split(',')))
            if len(location) != 2:
                raise ValueError("Invalid location format")
        except Exception as e:
            print(f"⚠️ Error reading location for {canteen}: {e}")
            location = [0, 0]  # Default to (0,0) if invalid

        if canteen not in keywords:     # Store extracted data in dictionaries
            keywords[canteen] = {}
            prices[canteen] = {}
            locations[canteen] = location

        keywords[canteen][stall] = keyword
        prices[canteen][stall] = price

    return keywords, prices, locations, df_canteen  # Return renamed variable


# Function to display all data from the Excel file
def display_all_data(): #Displays all food stall information from the dataset.

    print(f"\n{BLUE}📜 Now displaying all available food stalls! 😋{RESET}\n")
    print(canteen_data.to_string(index=False))  # This remains in white (default color)

    while True:
        user_input = input(f"\n{BLUE}Type 'back' to return to the main menu: {RESET}").strip().lower()
        if user_input == "back":
            return
        else:
            print(f"{BLUE}⚠️ Invalid input! 😔 Please type 'back' to return.{RESET}")


# Function to get user locations using PyGame
def get_user_location_interface(): # Allows a user to select a single location on an NTU campus map. The window will automatically close after one selection.

    # Load images for map and pin
    image_path = str(pathlib.Path(__file__).parent.resolve()) + "\\NTUcampus.jpg"
    pin_path = str(pathlib.Path(__file__).parent.resolve()) + "\\pin.png"

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("NTU Map - Select Your Location")

    map_image = pygame.image.load(image_path)
    map_image = pygame.transform.scale(map_image, (800, 600))
    pin_image = pygame.image.load(pin_path)
    pin_image = pygame.transform.scale(pin_image, (40, 40))

    screen.blit(map_image, (0, 0))
    pygame.display.flip()

    print(f"\n{BLUE}Click on the map to select your location. The window will close after selection.")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos  # Capture the user's click position
                screen.blit(pin_image, (x - 20, y - 40))  # Place pin at clicked location
                pygame.display.flip()
                time.sleep(0.5)  # Brief pause to show the pin before closing
                pygame.quit()
                return x, y  # Return coordinates of selected location

# Function to search by keyword
def search_by_keyword(): #    Searches for food stalls based on user input keywords with AND/OR functionality.

    while True:
        # Collect all available food keywords
        available_keywords = set()
        for stalls in canteen_stall_keywords.values():
            for stall_keywords in stalls.values():
                available_keywords.update(stall_keywords.split(", "))

        print(f"\n{BLUE}Here are the available food keywords:{RESET}")
        print(", ".join(sorted(available_keywords)))  # Ensuring this remains in white

        keywords = input(f"\n{BLUE}Please enter your desired food type (or type 'back' to return): {RESET}").strip().lower()
        if keywords == "back":
            return

        # Parse AND/OR logic
        parsed_terms = parse_keywords(keywords)

        # Check if any part of the search is valid
        all_valid = all(
            any(keyword in available_keywords for keyword in and_group)
            for and_group in parsed_terms["OR"]
        )

        # If no valid stalls match, suggest alternatives
        if not all_valid:
            # Find the closest matching keyword using fuzzy matching
            suggested_keywords = difflib.get_close_matches(keywords, available_keywords, n=3, cutoff=0.6)

            if suggested_keywords:
                print(
                    f"\n{BLUE}⚠️ No stalls serve your requested food type(s). Did you mean: {', '.join(suggested_keywords)}?{RESET}")
            else:
                print(f"\n{BLUE}⚠️ No stalls serve your requested food type(s). Please try again.{RESET}")
            continue  # Restart loop and ask again

        # Search for matching stalls with match count
        results = []
        for canteen, stalls in canteen_stall_keywords.items():
            for stall, stall_keywords in stalls.items():
                stall_keywords_set = set(stall_keywords.split(", "))

                match_count = 0  # Count how many groups this stall matches
                for and_group in parsed_terms["OR"]:
                    if all(kw in stall_keywords_set for kw in and_group):
                        match_count += len(and_group)  # Add the number of keywords matched in AND group

                if match_count > 0:
                    results.append((canteen, stall, match_count))

        if results:
            # Sort by match_count (descending)
            results.sort(key=lambda x: x[2], reverse=True)

            print(f"\n{BLUE}🍽 Food Stalls Found (Ranked by Relevance):{RESET}")
            for i, (canteen, stall, count) in enumerate(results, 1):
                print(f"{i}. {canteen} - {stall} (Matched {count} keyword{'s' if count > 1 else ''})")

        else:
            print(f"\n{BLUE}❌ No food stalls match your keywords. 😔{RESET}")


# Function to search by price
def search_by_price(): # Searches for food stalls based on user-provided keywords and max price, supporting AND/OR search logic.

    while True:
        # Collect all available food types (keywords from stalls)
        available_food_types = set()
        for stalls in canteen_stall_keywords.values():
            for stall_keywords in stalls.values():
                available_food_types.update(stall_keywords.split(", "))

        print(f"\n{BLUE}Available Food Types:{RESET}")
        print(", ".join(sorted(available_food_types)))  # Ensuring this remains in white

        # Get user input for food type
        food_type = input(f"\n{BLUE}Please enter your desired food type (or type 'back' to return): {RESET}").strip().lower()
        if food_type == "back":
            return

        # Parse AND/OR logic
        parsed_terms = parse_keywords(food_type)

        # Filter stalls that match at least one OR condition
        matching_stalls = []
        for canteen, stalls in canteen_stall_keywords.items():
            for stall, stall_keywords in stalls.items():
                stall_keywords_set = set(stall_keywords.split(", "))

                # Check if the stall satisfies (A and B) or (C)
                if any(all(kw in stall_keywords_set for kw in and_group) for and_group in parsed_terms["OR"]):
                    matching_stalls.append((canteen, stall))

        # Reject input if no stalls match the keyword conditions
        if not matching_stalls:
            # Find the closest matching keyword using fuzzy matching
            suggested_keywords = difflib.get_close_matches(food_type, available_food_types, n=3, cutoff=0.6)

            if suggested_keywords:
                print(
                    f"{BLUE}\n⚠️ No stalls serve your requested food type(s). Did you mean: {', '.join(suggested_keywords)}?{RESET}")
            else:
                print(f"{BLUE}\n⚠️ No stalls serve your requested food type(s). Please try again.{RESET}")
            continue  # Restart loop and ask again

        try:
            max_price = float(input(f"{BLUE}Please enter the maximum amount you're willing to spend 💸 (or type 'back' to return): {RESET}").strip())
            if max_price < 0:
                print(f"{BLUE}\n⚠️ No one's paying you to eat! 😠 Please input a positive value.{RESET}")
                continue
        except ValueError:
            print(f"\n{BLUE}⚠️ Invalid price! 😔 Please enter a valid number.{RESET}")
            continue

        results = []
        for canteen, stall in matching_stalls:
            price = canteen_stall_prices[canteen][stall]

            # Check if stall is within price range
            if price <= max_price:
                results.append((canteen, stall, price))

        if results:
            results.sort(key=lambda x: x[2])  # Sort by price
            print(f"\n{BLUE}💰 Affordable Food Stalls:{RESET}")
            for i, (canteen, stall, price) in enumerate(results, 1):
                print(f"{i}. {canteen} - {stall}: S${price:.2f}")        # Ensuring this remains in white
        else:
            # Find the stall with the closest price to the user's input
            closest_price_stall = None
            lowest_difference = float("inf")

            for canteen, stall in matching_stalls:
                price = canteen_stall_prices[canteen][stall]
                price_diff = abs(price - max_price)
                if price_diff < lowest_difference:
                    lowest_difference = price_diff
                    closest_price_stall = (canteen, stall, price)

            if closest_price_stall:
                print(f"\n{BLUE}⚠️ A wise man once said that there is no free lunch in the world.{RESET}")
                print(f"{BLUE}However, here is the store with the closest price point to your desired expenditure! 🍜{RESET}")
                print(f"1. {closest_price_stall[0]} - {closest_price_stall[1]}: S${closest_price_stall[2]:.2f}")  # Ensuring this remains in white
            else:
                print(f"\n{BLUE}❌ No affordable stalls found.{RESET}")


# Function to find nearest canteens
def search_nearest_canteens():
    """
    Asks user whether to input 1 or 2 locations, collects the locations,
    and displays the k nearest canteens based on distance.
    """
    print(f"\n{BLUE}📍 Location Proximity Search:{RESET}")
    while True:
        mode = input(f"{BLUE}Do you want to search using 1 or 2 user locations? Enter 1 or 2: {RESET}").strip()
        if mode not in ["1", "2"]:
            print(f"{BLUE}⚠️ Please enter either '1' or '2'.{RESET}")
            continue
        else:
            break

    print(f"{BLUE}Please select location(s) on the map...{RESET}")

    if mode == "1":
        user_location = get_user_location_interface()
        if user_location is None:
            print(f"{BLUE}⚠️ No location selected. Returning to main menu.{RESET}")
            return
        user_locations = [user_location]

    else:
        print(f"{BLUE}User A, select your location.{RESET}")
        user_a = get_user_location_interface()
        if user_a is None:
            print(f"{BLUE}⚠️ No location selected. Returning to main menu.{RESET}")
            return

        print(f"{BLUE}User B, select your location.{RESET}")
        user_b = get_user_location_interface()
        if user_b is None:
            print(f"{BLUE}⚠️ No location selected. Returning to main menu.{RESET}")
            return

        user_locations = [user_a, user_b]

    try:
        k = int(input(f"\n{BLUE}Enter the number of nearest canteens to display: {RESET}").strip())
        if k <= 0:
            print(f"{BLUE}⚠️ Warning: k cannot be negative. Defaulting to k = 1.{RESET}")
            k = 1
    except ValueError:
        print(f"\n{BLUE}⚠️ Invalid input! Defaulting to k = 1.{RESET}")
        k = 1

    # Calculate average distance from all provided user locations
    distances = []
    for canteen, coord in canteen_locations.items():
        total_dist = sum(((ux - coord[0]) ** 2 + (uy - coord[1]) ** 2) ** 0.5 for ux, uy in user_locations)
        avg_dist = total_dist / len(user_locations)
        distances.append((canteen, avg_dist))

    distances.sort(key=lambda x: x[1])
    print(f"\n{BLUE}📍 {k} Nearest Canteen{'s' if k > 1 else ''} Found:{RESET}")
    for i, (canteen, dist) in enumerate(distances[:k], 1):
        print(f"{i}. {canteen} – {dist:.0f}m")


# Load data from Excel files
canteen_stall_keywords, canteen_stall_prices, canteen_locations, canteen_data = load_canteen_data(DATA_FILE)

# Game-like exit logic
def confirm_exit(): #    Finds the nearest canteens based on user-selected location.

    while True:
        confirm = input(f"\n{BLUE}Are you sure you want to quit? (yes/no): {RESET}").strip().lower()
        if confirm == "yes":
            print(f"\n{PURPLE}🔚 Now closing NTU F&B Search Engine. Hope you get hungry again soon! 🍜{RESET}")
            exit()
        elif confirm == "no":
            return  # Return to the main menu
        else:
            print(f"\n{BLUE}⚠️ Invalid input! Please type 'yes' or 'no'.")

# Main program
def main():
    print(f"\n{PURPLE}🎉 Welcome to NTU F&B Search Engine! 🎉{RESET}")
    while True:
        print(f"\n{BLUE}To start, please choose one of the options below 👇{RESET}")
        print("1: Display All Food Stall Information")
        print("2: Keyword Search")
        print("3: Price Search")
        print("4: Location Proximity Search")
        print("5: Exit Search Engine")
        option = input(f"{BLUE}Enter your choice here: {RESET}").strip().lower()

        if option == "1":
            display_all_data()
        elif option == "2":
            search_by_keyword()
        elif option == "3":
            search_by_price()
        elif option == "4":
            search_nearest_canteens()
        elif option == "5":
            confirm_exit()
        else:
            print(f"\n⚠️ {BLUE}Invalid choice! Please try again. 😔{RESET}")


main()

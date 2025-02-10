import subprocess
import re
from collections import Counter
from itertools import combinations
import time

card_values = {
    'A': 11,  # Ace can be 1 or 11, but we'll use 11 here and adjust later
    'K': 10,
    'Q': 10,
    'J': 10,
    '10': 10,
    '9': 9,
    '8': 8,
    '7': 7,
    '6': 6,
    '5': 5,
    '4': 4,
    '3': 3,
    '2': 2
}

def update_html():
    """
    Get html of the current page in Safari

    Returns:
    str: HTML content of the current page
    """
    script = '''
    tell application "Safari"
        set pageHTML to do JavaScript "document.documentElement.outerHTML" in front document
        return pageHTML
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)

    with open("data/html/page_data.html", "w") as f:
        f.write(result.stdout)
    
    return result.stdout

def get_score():
    """
    Get the current score from the HTML content

    Args:
    html (str): HTML content of the page

    Returns:
    str: The current score
    """
    with open("data/html/page_data.html", "r") as f:
        html = f.read()
    pattern = r'<span class="weight-semibold line-height-default align-left size-default text-size-default variant-highlighted numeric with-icon-space is-truncate svelte-17v69ua" style="max-width: 16ch;">([\d,]+\.\d{2})</span>'
    match = re.search(pattern, html)
    if match:
        return float(match.group(1).replace(",", ""))
    return None

def get_cards(max_retries=10, delay=0.1):
    retries = 0
    
    while retries < max_retries:
        with open("data/html/page_data.html", "r") as f:
            html = f.read()
        
        pattern = r'<span>([AKQJ2-9]|10)</span>'
        matches = re.findall(pattern, html)
        matches = matches[5:]  # Skip the first five matches

        if len(matches) >= 2:
            return {
                "dealer": matches[0],
                "player": matches[1:]
            }

        retries += 1
        time.sleep(delay)

    # If we reach here, we failed to get enough cards
    return None  # or raise an Exception

def _value_hand(hand):
    # Calculate the value of the hand
    total = 0
    aces = 0
    for card in hand:
        if card in ['J', 'Q', 'K']:
            total += 10
        elif card == 'A':
            aces += 1
            total += 11
        else:
            total += int(card)

    # Adjust for aces if necessary
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def move_available():
    # Check if the "Hit" button is available
    with open("data/html/page_data.html", "r") as f:
        html = f.read()
    return not '<button type="button" tabindex="0" class="inline-flex relative items-center gap-2 justify-center rounded-sm font-semibold whitespace-nowrap ring-offset-background transition disabled:pointer-events-none disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 active:scale-[0.98] bg-green-500 text-neutral-black betterhover:hover:bg-green-400 betterhover:hover:text-neutral-black focus-visible:outline-white text-base leading-none shadow-md py-[1.125rem] px-[1.75rem]" data-testid="bet-button" data-test="bet-button" data-analytics="bet-button" data-test-action-enabled="true" data-button-root=""> <div data-loader-content="" class="contents"><span>Play</span></div></button>' in html

double_down_count = 0

def best_move(cards=None):
    global double_down_count  # To modify the global counter

    # Update the HTML page and check for insurance first.
    update_html()
    with open("data/html/page_data.html", "r") as f:
        page = f.read()
    # If the dealer’s upcard is an Ace (or the page suggests an insurance offer),
    # return "Insurance" and reset double down counter.
    if "Accept Insurance" in page or "Accept insurance" in page:
        double_down_count = 0
        return "Insurance"
    
    # If cards already include split hands (overloaded into the "Insurance" signal),
    # process each hand separately.
    if cards and "player_left" in cards and "player_right" in cards:
        left_move = best_move({
            'player': cards['player_left'],
            'dealer': cards['dealer']
        })
        right_move = best_move({
            'player': cards['player_right'],
            'dealer': cards['dealer']
        })
        return {"left": left_move, "right": right_move}
    
    # Get cards if not provided.
    cards = get_cards() if cards is None else cards
    if not cards:
        double_down_count = 0
        return "None"
    
    # Make sure a move is allowed.
    if not move_available():
        double_down_count = 0
        return "None"

    try:
        player_hand = cards['player']
        dealer_upcard = cards['dealer']
        # Determine dealer value (Ace is counted as 11).
        dealer_value = _value_hand([dealer_upcard])
        dealer = dealer_value  # For easier comparisons
        
        # --- Splitting Logic ---
        # Check if the player's hand can be split.
        if len(player_hand) == 2:
            card1 = player_hand[0].upper()
            card2 = player_hand[1].upper()
            ten_cards = {"10", "J", "Q", "K"}
            # Check for a pair (or pair of tens)
            if card1 == card2 or (card1 in ten_cards and card2 in ten_cards):
                split_possible = False
                # Basic splitting rules:
                if card1 == "A":  # Always split aces.
                    split_possible = True
                elif card1 == "8":  # Always split 8's.
                    split_possible = True
                elif card1 == "9":
                    # Split 9's if dealer shows 2-6 or 8-9 but not 7.
                    if dealer in [2, 3, 4, 5, 6, 8, 9]:
                        split_possible = True
                elif card1 == "7":
                    # Split 7's if dealer shows 2-7.
                    if dealer in [2, 3, 4, 5, 6, 7]:
                        split_possible = True
                elif card1 == "6":
                    # Split 6's if dealer shows 2-6.
                    if dealer in [2, 3, 4, 5, 6]:
                        split_possible = True
                elif card1 in {"2", "3"}:
                    # Split 2's and 3's if dealer shows 4-7.
                    if dealer in [4, 5, 6, 7]:
                        split_possible = True
                elif card1 == "4":
                    # Some strategies suggest splitting 4's against a 5-6.
                    if dealer in [5, 6]:
                        split_possible = True

                # Overload "Insurance" for both actual insurance offers and for splits.
                if split_possible:
                    double_down_count = 0
                    return "Insurance"
        
        # Compute player's hand total; _value_hand returns the optimal total.
        player_value = _value_hand(player_hand)
        
        # Return immediately if the player has a natural blackjack.
        if len(player_hand) == 2 and player_value == 21:
            double_down_count = 0
            return "None"
        
        # Helper: determine if the hand is soft (contains an Ace counted as 11).
        def is_soft(hand, value):
            return any(card.upper() == "A" for card in hand) and (value + 10 <= 21)
        
        soft = is_soft(player_hand, player_value)
        soft_total = player_value + 10 if soft else None
        
        # --- Soft Hand Strategy ---
        if soft:
            # Soft 13-14 (A2, A3): Double vs dealer 5-6; otherwise hit.
            if soft_total in [13, 14]:
                move = "Double Down" if dealer in [5, 6] else "Hit"
            # Soft 15-16 (A4, A5): Double vs dealer 4-6; otherwise hit.
            elif soft_total in [15, 16]:
                move = "Double Down" if dealer in [4, 5, 6] else "Hit"
            # Soft 17 (A6): Double vs dealer 3-6; otherwise hit.
            elif soft_total == 17:
                move = "Double Down" if dealer in [3, 4, 5, 6] else "Hit"
            # Soft 18 (A7): 
            #   - Double vs dealer 3-6,
            #   - Stand vs dealer 2, 7, or 8,
            #   - Hit vs dealer 9, 10, or Ace.
            elif soft_total == 18:
                if dealer in [3, 4, 5, 6]:
                    move = "Double Down"
                elif dealer in [2, 7, 8]:
                    move = "Stand"
                else:
                    move = "Hit"
            else:
                # For soft 19 or higher, always stand.
                move = "Stand"
        
        # --- Hard Hand Strategy ---
        else:
            # 17 or more: always stand.
            if player_value >= 17:
                move = "Stand"
            # 13 to 16: stand if dealer shows 2-6, otherwise hit.
            elif 13 <= player_value <= 16:
                move = "Stand" if dealer in [2, 3, 4, 5, 6] else "Hit"
            # 12: stand if dealer shows 4-6; hit otherwise.
            elif player_value == 12:
                move = "Stand" if dealer in [4, 5, 6] else "Hit"
            # 11: always double down.
            elif player_value == 11:
                move = "Double Down"
            # 10: double down if dealer shows 2 through 9; otherwise hit.
            elif player_value == 10:
                move = "Double Down" if 2 <= dealer <= 9 else "Hit"
            # 9: double down if dealer shows 3 through 6; otherwise hit.
            elif player_value == 9:
                move = "Double Down" if dealer in [3, 4, 5, 6] else "Hit"
            else:
                # 8 or less: always hit.
                move = "Hit"
        
        # --- Consecutive Double Down Check ---
        if move == "Double Down":
            if double_down_count >= 3:
                # Avoid the fourth consecutive double down.
                move = "Hit"
                double_down_count = 0
            else:
                double_down_count += 1
        else:
            double_down_count = 0
        
        return move

    except Exception as e:
        double_down_count = 0
        return "None"


def notify(message="Empty"):
    script = f'display notification "{message}" with title "Setup Helper"'
    subprocess.run(["osascript", "-e", script], check=True)
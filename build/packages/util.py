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

def get_cards(max_retries=50, delay=0.1):
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

# Global counter to track consecutive Double Down moves.
double_down_count = 0

def best_move(cards=None):
    global double_down_count  # To modify the global counter

    # Update the HTML page and check for insurance first.
    update_html()
    with open("data/html/page_data.html", "r") as f:
        page = f.read()
    if "Accept Insurance" in page or "Accept insurance" in page:
        # Reset the counter because we're not doubling down here.
        double_down_count = 0
        return "Insurance"
    
    # Get cards if not provided.
    cards = get_cards() if cards is None else cards
    if not cards:
        double_down_count = 0
        return "No cards detected"
    
    # Make sure a move is allowed.
    if not move_available():
        double_down_count = 0
        return "None"
    
    try:
        player_hand = cards['player']
        dealer_upcard = cards['dealer']
        
        # Compute the basic value of the player’s hand.
        # _value_hand should return the best total (counting Ace as 1 or 11).
        player_value = _value_hand(player_hand)
        # For the dealer, assume _value_hand returns 11 for an Ace.
        dealer_value = _value_hand([dealer_upcard])
        
        # Immediately return if the player has a natural blackjack.
        if len(player_hand) == 2 and player_value == 21:
            double_down_count = 0
            return "None"
        
        # Helper: determine if the player hand is "soft"
        # (i.e. contains an Ace that can be counted as 11 without busting)
        def is_soft(hand, value):
            return any(card.upper() == "A" for card in hand) and (value + 10 <= 21)
        
        soft = is_soft(player_hand, player_value)
        # If soft, calculate the soft total.
        soft_total = player_value + 10 if soft else None

        # For easier dealer comparisons, note that if dealer_value is 11, we treat it as Ace.
        dealer = dealer_value  # dealer_value==11 indicates an Ace
        
        # Initialize move decision.
        move = "Hit"  # default action
        
        # --- Soft Hand Strategy ---
        if soft:
            # Soft 13-14 (A2, A3): Double vs dealer 5-6; otherwise hit.
            if soft_total in [13, 14]:
                if dealer in [5, 6]:
                    move = "Double Down"
                else:
                    move = "Hit"
            # Soft 15-16 (A4, A5): Double vs dealer 4-6; otherwise hit.
            elif soft_total in [15, 16]:
                if dealer in [4, 5, 6]:
                    move = "Double Down"
                else:
                    move = "Hit"
            # Soft 17 (A6): Double vs dealer 3-6; otherwise hit.
            elif soft_total == 17:
                if dealer in [3, 4, 5, 6]:
                    move = "Double Down"
                else:
                    move = "Hit"
            # Soft 18 (A7):
            #   - Double vs dealer 2-6,
            #   - Stand vs dealer 7 or 8,
            #   - Hit vs dealer 9, 10, or Ace.
            elif soft_total == 18:
                if dealer in [2, 3, 4, 5, 6]:
                    move = "Double Down"
                elif dealer in [7, 8]:
                    move = "Stand"
                else:
                    move = "Hit"
            # Soft 19 or higher: always stand.
            else:
                move = "Stand"
        
        # --- Hard Hand Strategy ---
        else:
            # 17 or more: always stand.
            if player_value >= 17:
                move = "Stand"
            # 13 to 16: stand if dealer shows 2-6, otherwise hit.
            elif 13 <= player_value <= 16:
                if dealer in [2, 3, 4, 5, 6]:
                    move = "Stand"
                else:
                    move = "Hit"
            # 12: stand if dealer shows 4-6; hit otherwise.
            elif player_value == 12:
                if dealer in [4, 5, 6]:
                    move = "Stand"
                else:
                    move = "Hit"
            # 11: double down against any dealer card except Ace.
            elif player_value == 11:
                if dealer == 11:
                    move = "Hit"
                else:
                    move = "Double Down"
            # 10: double down if dealer shows 2 through 9.
            elif player_value == 10:
                if 2 <= dealer <= 9:
                    move = "Double Down"
                else:
                    move = "Hit"
            # 9: double down if dealer shows 3 through 6.
            elif player_value == 9:
                if dealer in [3, 4, 5, 6]:
                    move = "Double Down"
                else:
                    move = "Hit"
            # For hands of 8 or less, always hit.
            else:
                move = "Hit"
        
        # --- Double Down Consecutive Check ---
        if move == "Double Down":
            # If this would be the fourth double down in a row, override with a hit.
            if double_down_count >= 3:
                move = "Hit"
                double_down_count = 0  # Reset counter after overriding
            else:
                double_down_count += 1
        else:
            # Reset counter if the move is not a double down.
            double_down_count = 0
        
        return move
    except Exception as e:
        double_down_count = 0
        return "None"

def notify(message="Empty"):
    script = f'display notification "{message}" with title "Setup Helper"'
    subprocess.run(["osascript", "-e", script], check=True)
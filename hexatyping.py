import curses
import time
import random
import os
import json

BIG_FONT = {
    '0': [r"  /----\  ", r" /      \ ", r"|   ||   |", r"|   ||   |", r" \      / ", r"  \----/  "],
    '1': [r"    /|    ", r"   / |    ", r"     |    ", r"     |    ", r"     |    ", r"  ------- "],
    '2': [r"  /----\  ", r"       /  ", r"      /   ", r"     /    ", r"    /     ", r"  /-------"],
    '3': [r"  /----\  ", r"       /  ", r"   ---/   ", r"       \  ", r"  \    /  ", r"   ----   "],
    '4': [r"   /   |  ", r"  /    |  ", r" /  ---|  ", r" |_____|  ", r"       |  ", r"       |  "],
    '5': [r"  ------- ", r"  |       ", r"  |-----\ ", r"        | ", r"  \     | ", r"   -----  "],
    '6': [r"  /-----\ ", r"  |       ", r"  |-----  ", r"  |     | ", r"  |     | ", r"  \-----/ "],
    '7': [r"  ------- ", r"       /  ", r"      /   ", r"     /    ", r"    /     ", r"   /      "],
    '8': [r"  /-----\ ", r"  |     | ", r"  >-----< ", r"  |     | ", r"  |     | ", r"  \-----/ "],
    '9': [r"  /-----\ ", r"  |     | ", r"  \-----| ", r"        | ", r"       /  ", r"  ----/   "]
}

SCORE_FILE = os.path.expanduser("~/.hexatyping_scores")

def load_scores():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, 'r') as f:
                return json.load(f)
        except: return {}
    return {}

def save_score(mode, wpm):
    scores = load_scores()
    if mode not in scores: scores[mode] = []
    scores[mode].append(int(wpm))
    scores[mode] = sorted(scores[mode], reverse=True)[:5]
    with open(SCORE_FILE, 'w') as f: json.dump(scores, f)

def get_sentence(mode, sub_mode=None):
    mode_map = {
        "Normal": "sentences.txt",
        "Symbols": "symbols.txt",
        "General Knowledge": "gk.txt",
        "Programming Knowledge": "prog_knowledge.txt",
        "OS Commands": "os_commands.txt"
    }
    
    base_dir = os.path.dirname(__file__)
    search_paths = [os.path.join(base_dir, "content"), "/usr/share/hexatyping/content/"]
    
    if mode == "Programming" and sub_mode:
        filename = f"programming/{sub_mode.lower()}.txt"
    else:
        filename = mode_map.get(mode, "sentences.txt")
    
    for p in search_paths:
        file_path = os.path.join(p, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = [l.strip() for l in f if l.strip()]
                if lines: return random.choice(lines)
                
    return f"missing file: {filename} 💀"

def draw_big_score(stdscr, score, y, x):
    s_score = str(int(score))
    for i in range(6):
        line = ""
        for digit in s_score:
            line += BIG_FONT.get(digit, ["          "] * 6)[i] + " "
        stdscr.addstr(y + i, x, line, curses.color_pair(1) | curses.A_BOLD)

def generic_menu(stdscr, title, options):
    curses.curs_set(0)
    while True:
        stdscr.clear()
        stdscr.addstr(2, 4, f"[ {title} ]", curses.A_BOLD | curses.color_pair(1))
        stdscr.addstr(3, 4, "Select an option:", curses.A_DIM)
        for i, opt in enumerate(options):
            stdscr.addstr(6 + i, 4, f"{i+1}. {opt}")
        stdscr.refresh()
        key = stdscr.getch()
        if ord('1') <= key <= ord(str(len(options))):
            return options[key - ord('1')]
        elif key == 27: return "Back"

def play_game(stdscr, mode, sub_mode=None):
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    
    target = get_sentence(mode, sub_mode)
    display_name = sub_mode if sub_mode else mode
    user_input = ""
    wpm_history = []
    start_time = None
    
    all_scores = load_scores().get(display_name, [])
    current_pb = all_scores[0] if all_scores else 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        current_time = time.time()
        elapsed = max(current_time - (start_time or current_time), 0.1)
        raw_wpm = (len(user_input) / 5) / (elapsed / 60)
        correct_chars = sum(1 for i, c in enumerate(user_input) if i < len(target) and c == target[i])
        accuracy = (correct_chars / max(len(user_input), 1)) * 100
        
        if start_time: wpm_history.append(raw_wpm)

        status = f" MODE: {display_name} | ACC: {int(accuracy)}% | PB: {current_pb} "
        stdscr.addstr(0, 0, status.center(w), curses.color_pair(3))

        stdscr.addstr(4, 4, target, curses.A_DIM)
        for i, c in enumerate(user_input):
            if i < len(target):
                color = curses.color_pair(1) if c == target[i] else curses.color_pair(2)
                stdscr.addstr(4, 4 + i, c, color | curses.A_BOLD)

        if start_time:
            graph = "".join([' ', '▂', '▃', '▄', '▅', '▆', '▇', '█'][min(int(v/15), 7)] for v in wpm_history[-(w-10):])
            stdscr.addstr(h-2, 2, f"SPEED: {graph}")

        stdscr.refresh()

        if len(user_input) >= len(target):
            stdscr.clear()
            final_wpm = (correct_chars / 5) / (elapsed / 60)
            save_score(display_name, final_wpm)
            
            draw_big_score(stdscr, final_wpm, 3, 4)
            stdscr.addstr(10, 4, f"FINAL WPM: {int(final_wpm)} | ACCURACY: {int(accuracy)}%", curses.A_BOLD)
            stdscr.addstr(12, 4, "r: Restart | m: Menu | Esc: Exit")
            
            stdscr.refresh()
            key = stdscr.getch()
            if key == ord('r'): return "restart"
            if key == ord('m'): return "menu"
            return "exit"

        key = stdscr.getch()
        if key == 27: return "exit"
        if not start_time: start_time = time.time()
        
        if key in (127, 8, curses.KEY_BACKSPACE):
            user_input = user_input[:-1]
        elif 32 <= key <= 126 and len(user_input) < len(target):
            user_input += chr(key)

def main(stdscr):
    main_options = ["Normal", "Programming", "Symbols", "General Knowledge", "Programming Knowledge", "OS Commands", "Exit"]
    prog_options = ["Python", "C++", "JavaScript", "Rust", "Bash", "Back"]
    
    while True:
        choice = generic_menu(stdscr, "HEXATYPING MAIN", main_options)
        
        if choice == "Exit": break
        
        sub = None
        if choice == "Programming":
            sub = generic_menu(stdscr, "SELECT LANGUAGE", prog_options)
            if sub == "Back": continue
            
        while True:
            result = play_game(stdscr, choice, sub)
            if result == "menu": break
            if result == "exit": return

if __name__ == "__main__":
    curses.wrapper(main)

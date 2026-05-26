import os
import sys
import time
from game_env import MathPuzzleEnv
from planner import LeWMPlanner

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    env = MathPuzzleEnv()
    planner = LeWMPlanner()
    
    current_state = env.reset()
    last_action = None
    last_surprise = 0.0
    show_hint = False
    message = "Welcome to LeWorldModel PoC TUI! Place blocks to solve the expression."
    
    while True:
        clear_screen()
        
        # 1. Title & Header
        print("\033[1m========================================================\033[0m")
        print("\033[1m              LEWORLDMODEL (LeWM) PUZZLE SIMULATOR      \033[0m")
        print("\033[1m========================================================\033[0m")
        print(f"Goal Equation:  \033[1;36m{env.expression}\033[0m  (Target: \033[1;32m{env.target_answer}\033[0m)")
        print()
        
        # 2. Render Slots
        slots_display = []
        for val in env.slots:
            if val == -1:
                slots_display.append("\033[2m_\033[0m")
            else:
                slots_display.append(f"\033[1;33m{val}\033[0m")
        print(f"Puzzle Slots:   [  " + "  ".join(slots_display) + "  ]")
        
        # Render floor blocks
        avail = [str(i) for i in range(10) if env.available_blocks[i]]
        print(f"Blocks on Floor: {', '.join(avail)}")
        print()
        
        # 3. Model Telemetry & Embeddings
        print("\033[1m--- LeWorldModel (JEPA) Latent Telemetry ---\033[0m")
        if planner.is_loaded:
            # Latent vector z
            import torch
            s_vec = torch.tensor(env.get_state_vector(current_state)).unsqueeze(0)
            z = planner.model.get_latent(s_vec).squeeze(0).detach().numpy()
            
            # Print truncated latent vector representation
            z_str = ", ".join([f"{val:.3f}" for val in z[:8]])
            print(f"Latent Embedding z (first 8/16 dims): [{z_str}, ...]")
            
            # Last transition surprise score
            if last_action is not None:
                # Color code surprise
                color_code = "\033[1;32m" # Green (low surprise)
                if last_surprise > 0.15:
                    color_code = "\033[1;31m" # Red (high surprise/implausible)
                elif last_surprise > 0.05:
                    color_code = "\033[1;33m" # Yellow (medium surprise)
                
                # Format action name
                act_name = "PLACE" if last_action[0] == 0 else "REMOVE"
                print(f"Last Action: {act_name}(slot={last_action[1]}, val={last_action[2]})")
                print(f"Transition Surprise Score: {color_code}{last_surprise:.5f}\033[0m")
            else:
                print("Last Action: None")
                print("Transition Surprise Score: N/A")
        else:
            print("\033[2m[Model weights not found. Run 'train_poc.py' first to initialize model telemetry.]\033[0m")
            
        print()
        
        # 4. AI Buddy speech bubble
        print("\033[1m--- AI Buddy Speech Bubble ---\033[0m")
        if show_hint:
            best_action = planner.plan_best_action(current_state, env)
            hint_msg = planner.generate_conceptual_hint(current_state, best_action)
            print(f"Buddy: \033[1;35m\"{hint_msg}\"\033[0m")
        else:
            print("Buddy: \033[2m\"Press [h] to ask me for a conceptual hint!\"\033[0m")
        print()
        
        # 5. Message Box
        if message:
            print(f"\033[1;34mMessage:\033[0m {message}")
            message = ""
        print("-" * 56)
        
        # 6. Check Win Condition
        if env.slots == env.target_digits:
            print("\033[1;32mCONGRATULATIONS! You solved the puzzle! \033[0m")
            print("Press [t] to reset, or [q] to quit.")
            print()
            
        # 7. Menu options
        print("\033[1mCommands:\033[0m")
        print("  \033[1m[p]\033[0m Place Block   \033[1m[r]\033[0m Remove Block   \033[1m[h]\033[0m Toggle AI Hint   \033[1m[t]\033[0m Reset Board   \033[1m[q]\033[0m Quit")
        print()
        
        choice = input("Enter command: ").strip().lower()
        
        if choice == 'q':
            print("Exiting simulator. Goodbye!")
            sys.exit(0)
            
        elif choice == 't':
            current_state = env.reset()
            last_action = None
            last_surprise = 0.0
            show_hint = False
            message = "Board reset."
            
        elif choice == 'h':
            show_hint = not show_hint
            
        elif choice == 'p':
            valid_actions = env.get_valid_actions()
            places = [act for act in valid_actions if act[0] == 0]
            if not places:
                message = "Error: No empty slots to place a block!"
                continue
                
            try:
                slot_str = input("Select slot index (0, 1, 2): ").strip()
                slot = int(slot_str)
                val_str = input("Select block value (0-9): ").strip()
                val = int(val_str)
                
                action = (0, slot, val)
                if action not in places:
                    message = f"Error: Action PLACE(slot={slot}, val={val}) is invalid!"
                else:
                    # Calculate surprise before moving (since surprise needs pre and post states)
                    prev_state = dict(current_state)
                    next_state, reward, done, info = env.step(action)
                    
                    if planner.is_loaded:
                        last_surprise = planner.get_surprise(prev_state, action, next_state, env)
                        
                    current_state = next_state
                    last_action = action
                    message = f"Placed block {val} in slot {slot}."
            except ValueError:
                message = "Error: Invalid inputs. Please enter numbers."
                
        elif choice == 'r':
            valid_actions = env.get_valid_actions()
            removes = [act for act in valid_actions if act[0] == 1]
            if not removes:
                message = "Error: No blocks are currently placed to remove!"
                continue
                
            try:
                slot_str = input("Select slot index (0, 1, 2) to remove block from: ").strip()
                slot = int(slot_str)
                
                # find block value
                val = env.slots[slot]
                action = (1, slot, val)
                
                if action not in removes:
                    message = f"Error: No block in slot {slot} to remove!"
                else:
                    prev_state = dict(current_state)
                    next_state, reward, done, info = env.step(action)
                    
                    if planner.is_loaded:
                        last_surprise = planner.get_surprise(prev_state, action, next_state, env)
                        
                    current_state = next_state
                    last_action = action
                    message = f"Removed block {val} from slot {slot}."
            except ValueError:
                message = "Error: Invalid input index."
                
        else:
            message = "Unknown command. Try [p], [r], [h], [t], or [q]."

if __name__ == "__main__":
    main()

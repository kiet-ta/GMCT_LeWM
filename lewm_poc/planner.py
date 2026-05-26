import torch
import numpy as np
import os
from game_env import MathPuzzleEnv
from lewm_model import LeWorldModel

# Hardcoded conceptual hints mapped to target states/actions
CONCEPTUAL_HINTS = {
    # Hints when slots are empty
    "empty": "The target is 100. We should start by placing the digit in the hundreds position.",
    
    # Hints for placing correct digits
    "place_hundreds": "Look for a block to fill the hundreds place. What number starts the value '100'?",
    "place_tens": "Now focus on the tens position. What digit do we need in the middle of 100?",
    "place_ones": "Almost there! Look for a block to fill the ones position at the end of 100.",
    
    # Hints for correcting errors (removing blocks)
    "remove_wrong_hundreds": "Look at the first slot. Is that number too large or too small for '100'?",
    "remove_wrong_tens": "Check the middle slot. Does it match the second digit of '100'?",
    "remove_wrong_ones": "Examine the last slot. Is that the right digit for the ones place of 100?",
    "generic_remove": "One of the blocks you placed doesn't seem to fit the target answer. Try removing it.",
    
    # Correct answer hint
    "solved": "Great job! The equation 2 x 50 = 100 is fully solved!"
}

class LeWMPlanner:
    def __init__(self, model_path="lewm_model.pth"):
        self.model = LeWorldModel()
        self.model_path = model_path
        self.is_loaded = False
        
        if os.path.exists(model_path):
            try:
                self.model.load_state_dict(torch.load(model_path))
                self.model.eval()
                self.is_loaded = True
                print(f"Planner successfully loaded trained model weights from '{model_path}'")
            except Exception as e:
                print(f"Error loading model weights: {e}")
        else:
            print(f"Warning: model weights '{model_path}' not found. Planner will run untrained.")

    def get_surprise(self, state, action, next_state, env):
        """
        Calculates the 'Surprise' score of a transition: L2 distance in latent space.
        Surprise = || E(s_next) - P(E(s), a) ||^2
        """
        if not self.is_loaded:
            return 0.0
            
        with torch.no_grad():
            s_vec = torch.tensor(env.get_state_vector(state)).unsqueeze(0)
            a_vec = torch.tensor(env.get_action_vector(action)).unsqueeze(0)
            ns_vec = torch.tensor(env.get_state_vector(next_state)).unsqueeze(0)
            
            # Predict
            z = self.model.get_latent(s_vec)
            z_next_pred = self.model.predict_next_latent(z, a_vec)
            
            # Actual
            z_next_true = self.model.get_latent(ns_vec)
            
            # L2 distance
            surprise = torch.sum((z_next_pred - z_next_true) ** 2).item()
            return surprise

    def plan_best_action(self, current_state, env):
        """
        Plans the best next action using the LeWorldModel.
        It simulates each valid action, uses the predictor to guess the next latent state,
        decodes it, and finds the action that results in a state closest to the target '100'.
        """
        valid_actions = env.get_valid_actions()
        if not valid_actions:
            return None
            
        if not self.is_loaded:
            # Fallback to simple random action if model is not trained yet
            return valid_actions[0]
            
        target_state_vec = env.get_state_vector({
            "slots": env.target_digits,
            "available_blocks": [True] * 10 # approximate
        })
        
        best_action = None
        min_distance = float('inf')
        
        with torch.no_grad():
            s_vec = torch.tensor(env.get_state_vector(current_state)).unsqueeze(0)
            z = self.model.get_latent(s_vec)
            
            for act in valid_actions:
                a_vec = torch.tensor(env.get_action_vector(act)).unsqueeze(0)
                
                # Predict next latent state using World Model
                z_next_pred = self.model.predict_next_latent(z, a_vec)
                
                # Decode the predicted latent state back to raw features
                decoded_ns = self.model.decode(z_next_pred).squeeze(0).numpy()
                
                # We calculate the distance between the decoded slots and the target slots
                # Slot features are the first 33 elements
                decoded_slots = decoded_ns[:33]
                target_slots = target_state_vec[:33]
                
                distance = np.mean((decoded_slots - target_slots) ** 2)
                
                if distance < min_distance:
                    min_distance = distance
                    best_action = act
                    
        return best_action

    def generate_conceptual_hint(self, current_state, best_action):
        """
        Translates the model-suggested action into a conceptual, open-ended hint.
        """
        if best_action is None:
            return CONCEPTUAL_HINTS["solved"]
            
        act_type, slot, val = best_action
        slots = current_state["slots"]
        
        if act_type == 0:  # PLACE
            if slot == 0:
                return CONCEPTUAL_HINTS["place_hundreds"]
            elif slot == 1:
                return CONCEPTUAL_HINTS["place_tens"]
            elif slot == 2:
                return CONCEPTUAL_HINTS["place_ones"]
        else:  # REMOVE
            if slot == 0 and slots[0] != 1:
                return CONCEPTUAL_HINTS["remove_wrong_hundreds"]
            elif slot == 1 and slots[1] != 0:
                return CONCEPTUAL_HINTS["remove_wrong_tens"]
            elif slot == 2 and slots[2] != 0:
                return CONCEPTUAL_HINTS["remove_wrong_ones"]
            else:
                return CONCEPTUAL_HINTS["generic_remove"]
                
        return "Think about the target equation. 2 times 50 equals what number?"

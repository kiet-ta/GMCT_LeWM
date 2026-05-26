import numpy as np

class MathPuzzleEnv:
    def __init__(self, expression="2 x 50 = ?", target_answer="100", num_slots=3):
        self.expression = expression
        self.target_answer = target_answer
        self.num_slots = num_slots
        self.target_digits = [int(d) for d in target_answer]
        self.reset()

    def reset(self):
        # -1 represents empty slot
        self.slots = [-1] * self.num_slots
        # Available number blocks on the floor: digits 0-9
        self.available_blocks = [True] * 10
        return self.get_state()

    def get_state(self):
        return {
            "slots": list(self.slots),
            "available_blocks": list(self.available_blocks)
        }

    def get_state_vector(self, state=None):
        """
        Converts a state dictionary into a flat 43-dimensional numpy array:
        - 3 slots * 11 features per slot (1 empty indicator + 10 digit indicators) = 33 features
        - 10 blocks * 1 feature (availability indicator: 0 or 1) = 10 features
        Total dimension = 43
        """
        if state is None:
            state = self.get_state()
        
        vector = []
        # Encode slots
        for val in state["slots"]:
            slot_vec = [0.0] * 11
            if val == -1:
                slot_vec[0] = 1.0  # Empty indicator
            else:
                slot_vec[val + 1] = 1.0  # Digit 0-9 indicator
            vector.extend(slot_vec)
            
        # Encode block availability
        for avail in state["available_blocks"]:
            vector.append(1.0 if avail else 0.0)
            
        return np.array(vector, dtype=np.float32)

    def get_valid_actions(self):
        """
        Returns list of valid actions in the form (action_type, slot_index, value)
        - Action Type: 0 for PLACE, 1 for REMOVE
        """
        actions = []
        # Place actions
        for s in range(self.num_slots):
            if self.slots[s] == -1: # Only place in empty slots
                for v in range(10):
                    if self.available_blocks[v]:
                        actions.append((0, s, v))
        # Remove actions
        for s in range(self.num_slots):
            if self.slots[s] != -1: # Only remove from filled slots
                actions.append((1, s, self.slots[s]))
                
        return actions

    def get_action_vector(self, action):
        """
        Encodes action (type, slot, val) into a flat 14-dimensional vector:
        - 2 features for type (one-hot: [place, remove])
        - 3 features for slot (one-hot: [slot0, slot1, slot2])
        - 9 features for value (not needed, let's use 10 features for value 0-9: total 15 features)
        Let's use 15 dimensions:
        - Action Type: 2-dim (0: PLACE, 1: REMOVE)
        - Slot index: 3-dim (one-hot for slot index)
        - Value: 10-dim (one-hot for value 0-9)
        """
        act_type, slot, val = action
        vec = [0.0] * 15
        
        # Action type
        if act_type == 0:
            vec[0] = 1.0
        else:
            vec[1] = 1.0
            
        # Slot index
        if 0 <= slot < self.num_slots:
            vec[2 + slot] = 1.0
            
        # Value
        if 0 <= val < 10:
            vec[5 + val] = 1.0
            
        return np.array(vec, dtype=np.float32)

    def step(self, action):
        """
        Executes action and returns (next_state, reward, done, info)
        """
        act_type, slot, val = action
        
        valid = False
        if act_type == 0:  # PLACE
            if self.slots[slot] == -1 and self.available_blocks[val]:
                self.slots[slot] = val
                self.available_blocks[val] = False
                valid = True
        elif act_type == 1:  # REMOVE
            if self.slots[slot] == val:
                self.slots[slot] = -1
                self.available_blocks[val] = True
                valid = True
                
        # Calculate reward
        is_correct = (self.slots == self.target_digits)
        reward = 1.0 if is_correct else 0.0
        done = is_correct
        
        return self.get_state(), reward, done, {"valid": valid}

    def render(self):
        display = []
        for val in self.slots:
            if val == -1:
                display.append("_")
            else:
                display.append(str(val))
        slots_str = " ".join(display)
        avail_str = ", ".join([str(i) for i in range(10) if self.available_blocks[i]])
        print(f"Expression: {self.expression}")
        print(f"Slots:      [ {slots_str} ]")
        print(f"Available:  {avail_str}")
        print("-" * 30)

if __name__ == "__main__":
    env = MathPuzzleEnv()
    env.render()
    env.step((0, 0, 1)) # Place 1 in slot 0
    env.render()
    env.step((0, 1, 0)) # Place 0 in slot 1
    env.render()
    env.step((0, 2, 0)) # Place 0 in slot 2
    env.render()

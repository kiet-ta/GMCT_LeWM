import os
import random
import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from game_env import MathPuzzleEnv
from lewm_model import LeWorldModel, compute_lewm_losses

def generate_dataset(num_transitions=2000):
    """
    Generates transition data (state, action, next_state) by running an agent in the simulator.
    Uses a mixture of random exploration and goal-directed moves to ensure balanced data.
    """
    env = MathPuzzleEnv()
    dataset = []
    
    state = env.reset()
    for _ in range(num_transitions):
        valid_actions = env.get_valid_actions()
        if not valid_actions:
            state = env.reset()
            valid_actions = env.get_valid_actions()
            
        # 60% chance of making a constructive move towards the answer "100"
        # 40% chance of making a random move
        chosen_action = None
        if random.random() < 0.6:
            # Look for a constructive action
            # e.g., placing 1 in slot 0, 0 in slot 1, 0 in slot 2
            constructive_actions = []
            for act in valid_actions:
                act_type, slot, val = act
                if act_type == 0:  # PLACE
                    # check if the digit matches what we need
                    if slot == 0 and val == 1:
                        constructive_actions.append(act)
                    elif slot == 1 and val == 0:
                        constructive_actions.append(act)
                    elif slot == 2 and val == 0:
                        constructive_actions.append(act)
                else:  # REMOVE
                    # remove if it doesn't match the target answer
                    if slot == 0 and val != 1:
                        constructive_actions.append(act)
                    elif slot == 1 and val != 0:
                        constructive_actions.append(act)
                    elif slot == 2 and val != 0:
                        constructive_actions.append(act)
                        
            if constructive_actions:
                chosen_action = random.choice(constructive_actions)
                
        if chosen_action is None:
            chosen_action = random.choice(valid_actions)
            
        # Get vector representations before the step
        state_vec = env.get_state_vector(state)
        action_vec = env.get_action_vector(chosen_action)
        
        # Take step
        next_state, reward, done, info = env.step(chosen_action)
        next_state_vec = env.get_state_vector(next_state)
        
        dataset.append((state_vec, action_vec, next_state_vec))
        
        if done:
            state = env.reset()
        else:
            state = next_state
            
    # Unpack
    states = np.array([x[0] for x in dataset], dtype=np.float32)
    actions = np.array([x[1] for x in dataset], dtype=np.float32)
    next_states = np.array([x[2] for x in dataset], dtype=np.float32)
    
    return states, actions, next_states

def train():
    print("--- 1. Generating Training Data ---")
    states, actions, next_states = generate_dataset(2500)
    print(f"Generated {len(states)} transitions.")
    
    # Create DataLoader
    states_t = torch.tensor(states)
    actions_t = torch.tensor(actions)
    next_states_t = torch.tensor(next_states)
    
    dataset = TensorDataset(states_t, actions_t, next_states_t)
    dataloader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    # Initialize Model & Optimizer
    model = LeWorldModel()
    optimizer = optim.Adam(model.parameters(), lr=0.005)
    
    print("\n--- 2. Training LeWorldModel (JEPA) ---")
    epochs = 40
    for epoch in range(1, epochs + 1):
        epoch_losses = []
        epoch_pred = []
        epoch_recon = []
        epoch_sig = []
        
        for batch_s, batch_a, batch_ns in dataloader:
            optimizer.zero_grad()
            
            # Forward & Loss calculation
            losses = compute_lewm_losses(model, batch_s, batch_a, batch_ns, reg_weight=0.01)
            loss = losses["total_loss"]
            
            loss.backward()
            optimizer.step()
            
            epoch_losses.append(loss.item())
            epoch_pred.append(losses["pred_loss"].item())
            epoch_recon.append(losses["reconstruction_loss"].item())
            epoch_sig.append(losses["sigreg_loss"].item())
            
        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch {epoch:02d}/{epochs} | "
                  f"Loss: {np.mean(epoch_losses):.4f} | "
                  f"Pred: {np.mean(epoch_pred):.4f} | "
                  f"Recon: {np.mean(epoch_recon):.4f} | "
                  f"SIGReg: {np.mean(epoch_sig):.4f}")
            
    # Save model weights
    save_path = "lewm_model.pth"
    torch.save(model.state_dict(), save_path)
    print(f"\nModel saved successfully to {save_path}")
    
    # --- 3. Evaluate Model Predictions ---
    print("\n--- 3. Verifying Prediction Accuracy ---")
    model.eval()
    with torch.no_grad():
        # Let's test a simple transition:
        # Start state: slots empty [_, _, _]
        # Action: PLACE 1 in slot 0
        env_test = MathPuzzleEnv()
        test_state = env_test.reset() # [_, _, _]
        test_act = (0, 0, 1) # place 1 in slot 0
        
        s_vec = torch.tensor(env_test.get_state_vector(test_state)).unsqueeze(0)
        a_vec = torch.tensor(env_test.get_action_vector(test_act)).unsqueeze(0)
        
        # True next state
        next_s_true, _, _, _ = env_test.step(test_act)
        ns_vec_true = env_test.get_state_vector(next_s_true)
        
        # Predicted next state representation
        z = model.get_latent(s_vec)
        z_next_pred = model.predict_next_latent(z, a_vec)
        ns_vec_pred = model.decode(z_next_pred).squeeze(0).numpy()
        
        # Calculate error
        error = np.mean((ns_vec_true - ns_vec_pred) ** 2)
        print(f"Reconstruction MSE: {error:.6f}")
        
        # Print decoded slots vs true slots
        # In state vector, slots 0 is first 11 elements
        decoded_slots = []
        for i in range(3):
            start = i * 11
            end = start + 11
            slot_prob = ns_vec_pred[start:end]
            predicted_val_idx = np.argmax(slot_prob)
            if predicted_val_idx == 0:
                decoded_slots.append(-1)
            else:
                decoded_slots.append(predicted_val_idx - 1)
                
        print(f"True state slots:      {next_s_true['slots']}")
        print(f"Model-predicted slots: {decoded_slots}")
        if next_s_true['slots'] == decoded_slots:
            print("SUCCESS: The LeWorldModel correctly predicted and decoded the state transition!")
        else:
            print("WARNING: Prediction does not match perfectly. More training may be needed.")

if __name__ == "__main__":
    train()

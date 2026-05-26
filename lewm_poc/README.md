# LeWorldModel (LeWM) Proof of Concept (PoC)

This directory contains a standalone Python Proof of Concept (PoC) demonstrating how Yann LeCun's **LeWorldModel (LeWM)** — a Joint-Embedding Predictive Architecture (JEPA) — can be successfully applied to guide players in a 3D block-placing arithmetic puzzle game.

---

## 📖 Theoretical Background & Core Architecture

### What is LeWorldModel?
A **World Model** learns a predictive representation of the environment. Unlike traditional reinforcement learning models that predict exact, high-dimensional observations (like raw screen pixels), **LeWM (JEPA)** encodes observations into a lower-dimensional latent space and predicts future latent states.

This project implements a complete JEPA pipeline tailored to represent our game states:

1. **State Encoder ($E_\theta(s) \to z$)**: Encodes a 43-dimensional one-hot representation of the puzzle state (including filled slots and available digits on the floor) into a 16-dimensional latent space ($z$).
2. **Transition Predictor ($P_\phi(z_t, a_t) \to \hat{z}_{t+1}$)**: Takes the current latent representation $z_t$ and a 15-dimensional one-hot representation of the action $a_t$ (e.g. `PLACE` or `REMOVE` at a specific slot index) and predicts the future latent state $\hat{z}_{t+1}$.
3. **State Decoder ($D_\psi(z) \to \hat{s}$)**: Reconstructs the physical state vector from its latent embedding. This is used to verify that the 16-dimensional latent space successfully preserves all semantic rules of the game board.
4. **SIGReg Loss (Standard Deviation Regularization)**: As detailed in the LeWorldModel paper, training a JEPA requires preventing **representation collapse** (where the encoder maps every state to a constant vector). We implement SIGReg:
   $$\mathcal{L}_{SIGReg} = - \sum_{i=1}^D \ln( \sigma_i + \epsilon )$$
   This penalizes latent dimensions that have low variance across a batch, forcing the model to learn a diverse and expressive embedding space.

---

## 🛠️ Proof of Applicability (How it Guides Players)

To prove that LeWorldModel is useful for in-game guidance, the PoC demonstrates two key features:

### 1. Surprise-Driven Hint Triggering (Prediction Error)
When a player makes an action, we compute the **Surprise Score** (prediction error in the latent space):
$$\text{Surprise} = \| \hat{z}_{t+1} - z_{t+1} \|^2$$
- If the player makes a logical move that leads toward the solution, the model predicts the outcome with **low surprise** (small error).
- If the player places an incorrect number block or performs a counter-productive action, the prediction error spike yields **high surprise**.
- In the actual game, when the surprise score exceeds a threshold, the AI Buddy detects that the player is struggling/making mistakes and automatically speaks to offer guidance.

### 2. Latent Space Planning
Using the trained model, we search through all valid actions in the current state. For each action, we use the Predictor to project the future latent state and select the action that lands closest to the target answer embedding (`100`). This demonstrates that the AI model successfully guides the search for the optimal path without hardcoding a graph of transitions.

### 3. Conceptual Guidance (High-Level Hints)
Once the planner decides the best action, the AI Buddy translates this action into a **conceptual hint** (such as guiding the player to think about place-values) rather than a direct instruction, encouraging active problem-solving:
- *Target Action:* `PLACE(slot=0, val=1)` $\to$ *Hint:* *"Look for a block to fill the hundreds place. What number starts the value '100'?"*
- *Target Action:* `REMOVE(slot=1, val=5)` $\to$ *Hint:* *"Check the middle slot. Does it match the second digit of '100'?"*

---

## 🚀 Installation & Setup

Ensure you have Python 3 installed. Navigate to the `lewm_poc/` directory and install the requirements:

```bash
pip install -r requirements.txt
```

---

## 🏋️ How to Train the AI

Train the LeWorldModel by running the training script:

```bash
python train_poc.py
```

### What happens during training:
1. The script simulates a player running through the puzzle to generate a dataset of 2,500 state transitions.
2. It trains the PyTorch model for 40 epochs using a joint loss of **Next-State Prediction**, **State Reconstruction**, and **SIGReg**.
3. It prints training statistics every 5 epochs showing the loss decreasing.
4. After completion, it runs a validation test on an unseen transition (e.g. placing `1` in an empty first slot) and verifies if the decoded prediction matches the true physical state.
5. The weights are saved to `lewm_model.pth`.

---

## 🎮 Play and Verify via Interactive TUI

Once training is complete, start the interactive terminal user interface:

```bash
python tui.py
```

### Features to observe in the TUI:
- **Latent Embedding ($z$):** Watch how the first 8 dimensions of the latent space shift dynamically as you place and remove blocks.
- **Surprise Score:** 
  - Place `1` in slot 0, then `0` in slot 1. The surprise score will remain **green (very low)** because this matches the model's expectations.
  - Place `9` in slot 2 (wrong answer). The surprise score will turn **yellow or red (high)** because the model detects an unexpected transition.
- **AI Buddy Hints:** Press **`[h]`** to toggle the AI Buddy's conceptual hints. The buddy will dynamically analyze the board and provide guidance.

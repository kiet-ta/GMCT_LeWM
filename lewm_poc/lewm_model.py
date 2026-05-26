import torch
import torch.nn as nn
import torch.nn.functional as F

class StateEncoder(nn.Module):
    """
    Encodes the 43-dimensional one-hot state vector into a low-dimensional latent space.
    """
    def __init__(self, state_dim=43, latent_dim=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, latent_dim)
        )
        
    def forward(self, state):
        return self.net(state)

class StateDecoder(nn.Module):
    """
    Decodes a latent embedding back into the 43-dimensional state representation.
    Helps prove that the latent space successfully preserves all information about the physical state.
    """
    def __init__(self, latent_dim=16, state_dim=43):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, state_dim)
        )
        
    def forward(self, latent):
        return self.net(latent)

class TransitionPredictor(nn.Module):
    """
    Predicts the next latent state embedding given the current latent embedding and action vector.
    """
    def __init__(self, latent_dim=16, action_dim=15):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim + action_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, latent_dim)
        )
        
    def forward(self, latent, action):
        inputs = torch.cat([latent, action], dim=-1)
        return self.net(inputs)

class LeWorldModel(nn.Module):
    def __init__(self, state_dim=43, action_dim=15, latent_dim=16):
        super().__init__()
        self.encoder = StateEncoder(state_dim, latent_dim)
        self.predictor = TransitionPredictor(latent_dim, action_dim)
        self.decoder = StateDecoder(latent_dim, state_dim)
        self.latent_dim = latent_dim
        
    def get_latent(self, state_tensor):
        return self.encoder(state_tensor)
        
    def predict_next_latent(self, latent_tensor, action_tensor):
        return self.predictor(latent_tensor, action_tensor)
        
    def decode(self, latent_tensor):
        return self.decoder(latent_tensor)

def compute_sigreg_loss(target_embeddings, eps=1e-4):
    """
    SIGReg (Standard Deviation Regularization) Loss from the LeWorldModel paper.
    Calculates the standard deviation of each latent dimension across the batch,
    and penalizes dimensions with low variance to prevent representation collapse.
    
    SIGReg = -sum(log(std_d + eps))
    """
    # Compute standard deviation across the batch dimension (dim=0)
    stds = torch.std(target_embeddings, dim=0)
    
    # Penalize low standard deviation to encourage representations to spread out
    sigreg_loss = -torch.log(stds + eps).sum()
    return sigreg_loss

def compute_lewm_losses(model, states, actions, next_states, reg_weight=0.1):
    """
    Computes predictions loss, reconstruction loss, and SIGReg loss.
    """
    # 1. Encode states
    z = model.get_latent(states)
    z_next_target = model.get_latent(next_states)
    
    # 2. Predict next latent embedding
    z_next_pred = model.predict_next_latent(z, actions)
    
    # 3. Prediction loss (L2 distance in latent space)
    pred_loss = F.mse_loss(z_next_pred, z_next_target)
    
    # 4. Reconstruction loss (to ensure latent space captures all state details)
    # We reconstruct the next state from the predicted latent space
    reconstructed_next = model.decode(z_next_pred)
    reconstruction_loss = F.mse_loss(reconstructed_next, next_states)
    
    # 5. SIGReg loss to prevent representation collapse
    sigreg_loss = compute_sigreg_loss(z_next_target)
    
    # Total loss
    total_loss = pred_loss + reconstruction_loss + reg_weight * sigreg_loss
    
    return {
        "total_loss": total_loss,
        "pred_loss": pred_loss,
        "reconstruction_loss": reconstruction_loss,
        "sigreg_loss": sigreg_loss
    }

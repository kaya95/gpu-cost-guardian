import torch
import torch.nn as nn
import torch.optim as optim

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}\n🔥 Starting HEAVY GPU training...")

# Dummy dataset
X = torch.randn(1000, 10).to(device)
y = torch.randn(1000, 1).to(device)

model = nn.Sequential(
    nn.Linear(10, 50),
    nn.ReLU(),
    nn.Linear(50, 1)
).to(device)

optimizer = optim.Adam(model.parameters(), lr=0.01)
criterion = nn.MSELoss()

for epoch in range(1, 21):
    optimizer.zero_grad()
    outputs = model(X)
    loss = criterion(outputs, y)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch} | Loss={loss.item():.4f}")

print("✅ Training complete.")

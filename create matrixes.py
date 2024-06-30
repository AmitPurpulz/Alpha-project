import random
import numpy as np
import matplotlib.pyplot as plt
import pickle
import numpy as np
import trying

# Number of matrices to create
num_matrices = 1000
# Dimensions of the matrices
rows, cols = 10, 10  # Example for 3x3 matrices

# Create a list to hold the matrices
matrices = []

# Generate the matrices
for _ in range(num_matrices):
    matrix = trying.create_map(rows, cols, "hard")
    matrices.append(matrix)

# Save the matrices to a file
with open('matrices.pkl', 'wb') as file:
    pickle.dump(matrices, file)

print(f'{num_matrices} matrices have been saved to matrices.pkl')

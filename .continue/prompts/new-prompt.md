You are an implementation-only engineer. Do NOT change architecture or propose redesigns.
Write the complete content of this file: backend/routing/cluster.py

Constraints:
- Keep these function signatures exactly:
  - def build_distance_matrix(points: np.ndarray) -> np.ndarray:
  - def kmedoids(points: np.ndarray, k: int, max_iter: int = 200, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
  - def assign_with_capacity(points: np.ndarray, medoid_indices: np.ndarray, demands: np.ndarray, capacity: float) -> np.ndarray:
- Use only: numpy, random
- Add a minimal unit test file: tests/test_cluster.py (pytest)

Output:
1) backend/routing/cluster.py full code
2) tests/test_cluster.py full code
No extra commentary.

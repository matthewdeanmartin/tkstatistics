# tkstatistics/stats/linalg_small.py

"""
A minimal, pure-Python linear algebra helper for small matrices.
Used for solving the normal equations in Ordinary Least Squares (OLS) regression.
No external dependencies.
"""
from __future__ import annotations


Matrix = list[list[float]]
Vector = list[float]


def transpose(matrix: Matrix) -> Matrix:
    """Transposes a matrix (list of lists)."""
    return [list(row) for row in zip(*matrix, strict=False)]


def matmul(A: Matrix, B: Matrix) -> Matrix:
    """Multiplies two matrices A and B."""
    n_rows_A = len(A)
    n_cols_A = len(A[0])
    n_rows_B = len(B)
    n_cols_B = len(B[0])

    if n_cols_A != n_rows_B:
        raise ValueError("Matrix dimensions are incompatible for multiplication.")

    result: Matrix = [[0.0] * n_cols_B for _ in range(n_rows_A)]

    for i in range(n_rows_A):
        for j in range(n_cols_B):
            for k in range(n_cols_A):
                result[i][j] += A[i][k] * B[k][j]
    return result


def matvec_mul(A: Matrix, v: Vector) -> Vector:
    """Multiplies a matrix A by a vector v."""
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]


def identity(n: int) -> Matrix:
    """Creates an n x n identity matrix."""
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def invert(matrix: Matrix) -> Matrix:
    """
    Inverts a square matrix using Gauss-Jordan elimination.
    Raises ValueError for non-square or singular matrices.
    """
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("Matrix must be square to be inverted.")

    # Augment the matrix with the identity matrix
    aug = [row + I_row for row, I_row in zip(matrix, identity(n), strict=False)]

    # Forward elimination (to get upper triangular form)
    for i in range(n):
        # Find pivot
        pivot_row = i
        for k in range(i + 1, n):
            if abs(aug[k][i]) > abs(aug[pivot_row][i]):
                pivot_row = k
        aug[i], aug[pivot_row] = aug[pivot_row], aug[i]

        pivot_val = aug[i][i]
        if abs(pivot_val) < 1e-12:  # Check for singularity
            raise ValueError("Matrix is singular and cannot be inverted.")

        # Normalize pivot row
        for j in range(i, 2 * n):
            aug[i][j] /= pivot_val

        # Eliminate other rows
        for k in range(n):
            if i == k:
                continue
            factor = aug[k][i]
            for j in range(i, 2 * n):
                aug[k][j] -= factor * aug[i][j]

    # The right half of the augmented matrix is now the inverse
    inv_matrix = [row[n:] for row in aug]
    return inv_matrix

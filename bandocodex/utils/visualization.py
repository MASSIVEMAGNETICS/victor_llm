# File: bandocodex/utils/visualization.py

"""
Visualization utilities for the BandoCosmicCodex.
Requires matplotlib to be installed.
"""

import numpy as np
from typing import Optional, Tuple

# Attempt to import matplotlib, provide a stub if not found.
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    # Provide stubs or raise informative errors if matplotlib is essential
    # For now, functions will check MATPLOTLIB_AVAILABLE.
    plt = None
    mcolors = None

def plot_fractal_grid(
    grid_data: np.ndarray,
    title: str = "Fractal Set",
    cmap: str = "magma", # Other good options: 'hot', 'twilight_shifted'
    x_range: Optional[Tuple[float, float]] = None,
    y_range: Optional[Tuple[float, float]] = None
) -> None:
    """
    Plots a 2D fractal grid using matplotlib.

    Args:
        grid_data (np.ndarray): The 2D numpy array containing iteration counts or fractal values.
        title (str): The title of the plot.
        cmap (str): The colormap to use for the plot.
        x_range (Optional[Tuple[float, float]]): The x-axis extent for the plot.
        y_range (Optional[Tuple[float, float]]): The y-axis extent for the plot.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib is not installed. Cannot plot fractal grid.")
        print(f"Title: {title}")
        print("Grid data (shape):", grid_data.shape)
        return

    plt.figure(figsize=(10, 8))

    img_extent = None
    if x_range and y_range:
        img_extent = [*x_range, *y_range]

    # Using a LogNorm for iteration counts can help reveal details
    # Handle cases where min value is 0 or all values are the same to avoid LogNorm errors
    min_val = np.min(grid_data[grid_data > 0]) if np.any(grid_data > 0) else 1
    max_val = grid_data.max() if grid_data.max() > 0 else 1
    if min_val >= max_val: # Avoid LogNorm error if all positive values are the same or no positive values
        norm = None
    else:
        norm = mcolors.LogNorm(vmin=min_val, vmax=max_val)

    plt.imshow(grid_data, cmap=cmap, origin='lower', norm=norm, extent=img_extent)

    plt.title(title)
    plt.xlabel("Re(c)" if "Mandelbrot" in title else "Re(z0)") # Assuming z0 for Julia
    plt.ylabel("Im(c)" if "Mandelbrot" in title else "Im(z0)")
    plt.colorbar(label="Iteration count") # Assuming iteration counts
    plt.show()


def plot_bloch_vector(
    vector: np.ndarray,
    title: str = "Bloch Sphere Representation"
) -> None:
    """
    Plots a 3D representation of a Bloch vector on the Bloch sphere.

    Args:
        vector (np.ndarray): A 3D numpy array [x, y, z] representing the Bloch vector.
        title (str): The title for the plot or output.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib is not installed. Cannot plot Bloch vector.")
        print(f"Title: {title}")
        print(f"Vector: {vector}")
        return

    if not isinstance(vector, np.ndarray) or vector.shape != (3,):
        print(f"Invalid Bloch vector provided. Expected a 3D numpy array. Got: {vector}")
        return

    x, y, z = vector

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Draw sphere
    u_sphere = np.linspace(0, 2 * np.pi, 100)
    v_sphere = np.linspace(0, np.pi, 100)
    sphere_x = np.outer(np.cos(u_sphere), np.sin(v_sphere))
    sphere_y = np.outer(np.sin(u_sphere), np.sin(v_sphere))
    sphere_z = np.outer(np.ones(np.size(u_sphere)), np.cos(v_sphere))
    ax.plot_surface(sphere_x, sphere_y, sphere_z, color='lightblue', alpha=0.2, rstride=4, cstride=4, linewidth=0)

    # Draw vector
    ax.quiver(0, 0, 0, x, y, z, length=1.0, color='r', arrow_length_ratio=0.1, label=f'State ({x:.2f}, {y:.2f}, {z:.2f})')

    # Axes lines
    ax.plot([-1.1, 1.1], [0, 0], [0, 0], color='gray', alpha=0.5, linestyle='--') # X-axis
    ax.plot([0, 0], [-1.1, 1.1], [0, 0], color='gray', alpha=0.5, linestyle='--') # Y-axis
    ax.plot([0, 0], [0, 0], [-1.1, 1.1], color='gray', alpha=0.5, linestyle='--') # Z-axis

    # Labels for axes and poles
    ax.text(1.15, 0, 0, 'X', color='black')
    ax.text(0, 1.15, 0, 'Y', color='black')
    ax.text(0, 0, 1.15, 'Z (|0⟩)', color='black')
    ax.text(0, 0, -1.25, '|1⟩', color='black')


    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(title)

    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])

    # Set view to look down z-axis slightly for a better initial 3D impression
    ax.view_init(elev=20., azim=30)

    plt.legend()
    plt.show()

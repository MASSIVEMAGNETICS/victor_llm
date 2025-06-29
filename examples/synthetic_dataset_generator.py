# File: examples/synthetic_dataset_generator.py

"""
Generates a synthetic dataset of (lyric, prosody_map) pairs
using the simplified components from bandocodex_components.py.

This script demonstrates how such components could be used.
The output is a JSON file where each entry is a dictionary:
{
    "lyric_id": "synth_00001",
    "lyric": "Generated lyric...",
    "prosody_map": { ... prosody data ... }
}
"""

import json
import argparse
from pathlib import Path
import time # For progress indication
import sys # For sys.exit

# Assuming bandocodex_components.py is in the same directory (examples/)
# or that the examples directory is in PYTHONPATH.
try:
    from bandocodex_components import LyricalFlowEngine, SimplifiedSFLM
except ImportError:
    # Fallback if running directly and examples/ is not in path automatically
    print("Attempting fallback import for bandocodex_components. Ensure examples/ is in PYTHONPATH or run from project root.")
    # This adds the directory of the current script to sys.path
    sys.path.append(str(Path(__file__).resolve().parent))
    from bandocodex_components import LyricalFlowEngine, SimplifiedSFLM


def generate_dataset(num_samples: int, output_path: Path) -> None:
    """
    Generates a dataset and saves it to a JSON file.

    Args:
        num_samples (int): The number of (lyric, prosody_map) pairs to generate.
        output_path (Path): The path to save the output JSON file.
    """
    print(f"Initializing dataset generation for {num_samples} samples...")
    lyric_engine = LyricalFlowEngine()
    sflm = SimplifiedSFLM()

    dataset = []

    generation_start_time = time.time()
    batch_start_time = time.time()

    for i in range(num_samples):
        lyric = lyric_engine.generate_lyric()
        prosody_map = sflm.generate_prosody_map(lyric)

        dataset.append({
            "lyric_id": f"synth_{i+1:05d}", # Add a unique ID
            "lyric": lyric,
            "prosody_map": prosody_map
        })

        if (i + 1) % 10 == 0 or (i + 1) == num_samples:
            batch_elapsed_time = time.time() - batch_start_time
            total_elapsed_time = time.time() - generation_start_time
            print(f"Generated {i + 1}/{num_samples} samples... (Batch took {batch_elapsed_time:.2f}s, Total: {total_elapsed_time:.2f}s)")
            batch_start_time = time.time() # Reset timer for next batch

    print(f"\nSaving dataset to {output_path}...")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True) # Ensure output directory exists
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=4)
        print(f"Successfully saved {len(dataset)} samples to {output_path}")
    except IOError as e:
        print(f"Error saving dataset: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during saving: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Synthetic Dataset Generator for BandoCodex Acoustic Model Training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--num_samples",
        "-n",
        type=int,
        default=100,
        help="Number of lyric/prosody pairs to generate."
    )
    parser.add_argument(
        "--output_file",
        "-o",
        type=str,
        default="acoustic_training_data.json",
        help="Name of the output JSON file. If not an absolute path, it's saved in the 'examples' directory."
    )

    args = parser.parse_args()

    # Determine output path
    output_file_path = Path(args.output_file)
    if not output_file_path.is_absolute():
        # Place it in the same directory as this script (examples/)
        output_path = Path(__file__).resolve().parent / output_file_path
    else:
        output_path = output_file_path

    if not isinstance(args.num_samples, int) or args.num_samples <= 0:
        print("Error: Number of samples must be a positive integer.")
        sys.exit(1) # Exit with an error code

    generate_dataset(args.num_samples, output_path)


if __name__ == "__main__":
    main()

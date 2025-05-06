#!/usr/bin/env python
"""Generate test fixtures for NeuroSpark Core tests."""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from tests.test_utils.data_generators import (
    generate_random_documents,
    generate_random_users,
    generate_random_messages,
    generate_random_embedding_points,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_fixtures(output_dir: str, count: int = 10) -> None:
    """Generate test fixtures.
    
    Args:
        output_dir: The output directory.
        count: The number of fixtures to generate.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate documents
    logger.info(f"Generating {count} documents")
    documents = generate_random_documents(count)
    with open(os.path.join(output_dir, "documents.json"), "w") as f:
        json.dump(documents, f, indent=2)
    
    # Generate users
    logger.info(f"Generating {count} users")
    users = generate_random_users(count)
    with open(os.path.join(output_dir, "users.json"), "w") as f:
        json.dump(users, f, indent=2)
    
    # Generate messages
    logger.info(f"Generating {count} messages")
    messages = generate_random_messages(count)
    with open(os.path.join(output_dir, "messages.json"), "w") as f:
        json.dump(messages, f, indent=2)
    
    # Generate embedding points
    logger.info(f"Generating {count} embedding points")
    embedding_points = generate_random_embedding_points(count)
    with open(os.path.join(output_dir, "embedding_points.json"), "w") as f:
        json.dump(embedding_points, f, indent=2)
    
    logger.info(f"Generated fixtures in {output_dir}")


def generate_hallucinations(output_dir: str, count: int = 10) -> None:
    """Generate hallucinations for reviewer testing.
    
    Args:
        output_dir: The output directory.
        count: The number of hallucinations to generate.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate hallucinations
    logger.info(f"Generating {count} hallucinations")
    
    hallucinations = []
    for i in range(count):
        hallucination = {
            "id": f"hall-{i+1:03d}",
            "original_text": f"This is the original text {i+1}.",
            "hallucinated_text": f"This is the hallucinated text {i+1}.",
            "explanation": f"This is the explanation for hallucination {i+1}.",
        }
        hallucinations.append(hallucination)
    
    with open(os.path.join(output_dir, "hallucinations.json"), "w") as f:
        json.dump(hallucinations, f, indent=2)
    
    logger.info(f"Generated hallucinations in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test fixtures")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="tests/fixtures",
        help="Output directory for fixtures",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of fixtures to generate",
    )
    parser.add_argument(
        "--hallucinations",
        action="store_true",
        help="Generate hallucinations for reviewer testing",
    )
    
    args = parser.parse_args()
    
    generate_fixtures(args.output_dir, args.count)
    
    if args.hallucinations:
        generate_hallucinations(args.output_dir, args.count)

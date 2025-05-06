#!/usr/bin/env python
"""Initialize the database with Alembic."""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from alembic.config import Config
from alembic import command

from src.database.connection import get_engine
from src.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(create_tables: bool = False, stamp_head: bool = False) -> None:
    """Initialize the database.
    
    Args:
        create_tables: Whether to create tables using SQLAlchemy.
        stamp_head: Whether to stamp the database with the head revision.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent.absolute()
    
    # Create the alembic.ini file path
    alembic_ini = os.path.join(project_root, "alembic.ini")
    
    if create_tables:
        logger.info("Creating database tables using SQLAlchemy")
        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    
    if stamp_head:
        logger.info("Stamping database with head revision")
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")
        logger.info("Database stamped with head revision")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the database")
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create tables using SQLAlchemy",
    )
    parser.add_argument(
        "--stamp-head",
        action="store_true",
        help="Stamp the database with the head revision",
    )
    
    args = parser.parse_args()
    
    init_db(create_tables=args.create_tables, stamp_head=args.stamp_head)

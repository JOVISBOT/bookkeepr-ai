"""Database Migration Script"""
from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade
from flask_sqlalchemy import SQLAlchemy
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from extensions import db, migrate
from app import create_app

def create_migration_app():
    """Create app for migrations"""
    return create_app(os.getenv('FLASK_ENV', 'development'))


if __name__ == '__main__':
    app = create_migration_app()
    
    with app.app_context():
        # Initialize migrations if not exists
        if not os.path.exists('migrations'):
            print("Initializing migrations...")
            init(app=app, db=db)
        
        # Create initial migration
        print("Creating migration...")
        migrate(app=app, db=db, message='Initial migration')
        
        # Upgrade database
        print("Upgrading database...")
        upgrade(app=app, db=db)
        
        print("Done!")

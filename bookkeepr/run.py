"""
BookKeepr AI - Entry Point
Run with: python run.py
"""
from app import create_app, db
from app.models import User, Company, Transaction, Account, CategoryRule
import os

app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Company': Company,
        'Transaction': Transaction,
        'Account': Account,
        'CategoryRule': CategoryRule
    }


@app.cli.command()
def test():
    """Run tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    print("🚀 Starting BookKeepr AI...")
    print("📁 Project: bookkeepr/")
    print("🔧 Environment:", os.getenv('FLASK_ENV', 'development'))
    print()
    print("Available routes:")
    print("  - /auth/connect      - Start QuickBooks OAuth")
    print("  - /                  - Dashboard (after login)")
    print("  - /api/v1/           - API endpoints")
    print()
    app.run(host='0.0.0.0', port=5000, debug=True)

"""Create test user"""
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    # Check if user exists
    user = User.query.filter_by(email='test@bookkeepr.ai').first()
    if not user:
        user = User(
            email='test@bookkeepr.ai',
            first_name='Test',
            last_name='User',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        print("Test user created!")
    else:
        print("User already exists")
    
    print(f"User ID: {user.id}")
    print(f"Email: {user.email}")

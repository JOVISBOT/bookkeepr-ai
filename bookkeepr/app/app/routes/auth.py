"""Authentication Routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__)


@bp.route('/login')
def login():
    """Login page"""
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/register')
def register():
    """Registration page"""
    return render_template('auth/register.html')


@bp.route('/forgot-password')
def forgot_password():
    """Password reset request"""
    return render_template('auth/forgot_password.html')

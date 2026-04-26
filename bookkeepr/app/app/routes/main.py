"""Main Routes"""
from flask import Blueprint, render_template, redirect, url_for, send_from_directory
from flask_login import login_required, current_user
import os

from app.models import Company, Transaction

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Landing page - show working HTML"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    else:
        return render_template('index.html')


@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

"""Main Routes"""
from flask import Blueprint, render_template, redirect, url_for

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Homepage"""
    return render_template('index.html')


@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

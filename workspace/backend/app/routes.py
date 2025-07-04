from flask import Blueprint, jsonify, request
from .models import User, db

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@bp.route('/users/<int:user_id>', methods=['POST'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'bio' in data:
        user.bio = data['bio']
    if 'profile_picture_url' in data:
        user.profile_picture_url = data['profile_picture_url']

    db.session.commit()
    return jsonify(user.to_dict())

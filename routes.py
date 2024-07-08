from flask import request, jsonify
from app import app, db
from models import User, Organisation
from schemas import UserSchema, OrganisationSchema
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import uuid

user_schema = UserSchema()
organisation_schema = OrganisationSchema()
organisation_list_schema = OrganisationSchema(many=True)


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    errors = user_schema.validate(data)
    if errors:
        return jsonify({"errors": [{"field": k, "message": v[0]} for k, v in errors.items()]}), 422

    user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    org_name = f"{user.first_name}'s Organisation"
    organisation = Organisation(name=org_name)
    organisation.users.append(user)
    db.session.add(organisation)
    db.session.commit()

    access_token = create_access_token(identity=str(user.user_id))
    return jsonify({
        'status': 'success',
        'message': 'Registration successful',
        'data': {
            'accessToken': access_token,
            'user': user_schema.dump(user)
        }
    }), 201


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=str(user.user_id))
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'accessToken': access_token,
                'user': user_schema.dump(user)
            }
        }), 200
    return jsonify({'status': 'Bad request', 'message': 'Authentication failed', 'statusCode': 401}), 401


@app.route('/api/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user and (user.user_id == current_user_id or any(org in user.organisations for org in User.query.get(current_user_id).organisations)):
        return jsonify({
            'status': 'success',
            'message': 'User retrieved successfully',
            'data': user_schema.dump(user)
        }), 200
    return jsonify({'status': 'Forbidden', 'message': 'You do not have permission to view this user'}), 403


@app.route('/api/organisations', methods=['GET', 'POST'])
@jwt_required()
def organisations():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if request.method == 'POST':
        data = request.get_json()
        errors = organisation_schema.validate(data)
        if errors:
            return jsonify({"errors": [{"field": k, "message": v[0]} for k, v in errors.items()]}), 422

        organisation = Organisation(name=data['name'], description=data.get('description'))
        organisation.users.append(user)
        db.session.add(organisation)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Organisation created successfully',
            'data': organisation_schema.dump(organisation)
        }), 201
    return jsonify({
        'status': 'success',
        'message': 'Organisations retrieved successfully',
        'data': organisation_list_schema.dump(user.organisations)
    }), 200


@app.route('/api/organisations/<org_id>', methods=['GET'])
@jwt_required()
def get_organisation(org_id):
    current_user_id = get_jwt_identity()
    organisation = Organisation.query.get(org_id)
    user = User.query.get(current_user_id)
    if organisation and user in organisation.users:
        return jsonify({
            'status': 'success',
            'message': 'Organisation retrieved successfully',
            'data': organisation_schema.dump(organisation)
        }), 200
    return jsonify({'status': 'Forbidden', 'message': 'You do not have permission to view this organisation'}), 403


@app.route('/api/organisations/<org_id>/users', methods=['POST'])
@jwt_required()
def add_user_to_organisation(org_id):
    current_user_id = get_jwt_identity()
    organisation = Organisation.query.get(org_id)
    if organisation and any(org in organisation.users for org in User.query.get(current_user_id).organisations):
        data = request.get_json()
        user = User.query.get(data['user_id'])
        if user:
            organisation.users.append(user)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'User added to organisation successfully'}), 200
        return jsonify({'status': 'Bad Request', 'message': 'User not found'}), 400
    return jsonify({'status': 'Forbidden', 'message': 'You do not have permission to add users to this organisation'}), 403

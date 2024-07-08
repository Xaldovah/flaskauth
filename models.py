from app import db
import uuid
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.String(36), primary_key=True, default=str(uuid.uuid4()), unique=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False, default='defaultpasswordhash')
    phone = db.Column(db.String(15))

    organisations = db.relationship('Organisation', secondary='user_organisation', back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Organisation(db.Model):
    __tablename__ = 'organisation'

    org_id = db.Column(db.String(36), primary_key=True, default=str(uuid.uuid4()), unique=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    users = db.relationship('User', secondary='user_organisation', back_populates='organisations')


class UserOrganisation(db.Model):
    __tablename__ = 'user_organisation'

    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), primary_key=True)
    org_id = db.Column(db.String(36), db.ForeignKey('organisation.org_id'), primary_key=True)

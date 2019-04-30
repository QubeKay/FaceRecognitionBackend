# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db

# Import password / encryption helper tools
from werkzeug import check_password_hash, generate_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True, autoincrement=True)
    username = db.Column(db.String(25), unique=True)
    name = db.Column(db.String(150))
    password = db.Column(db.String(191))
    embeddings = db.Column(db.Text())

    def __init__(self, username=None, password=None, name=None, embeddings=None):
        self.username = username
        self.name = name
        self.embeddings = embeddings
        self.password = generate_password_hash(password)

    def __repr__(self):
        return "<User(id=%d, username='%s', name='%s', password='%s', embeddings='%s')>" % \
               (self.id, self.username, self.name, self.password, self.embeddings)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'password': self.password,
            'embeddings': self.embeddings
        }

    def check_password(self, password):
        check_password_hash(self.password, password)
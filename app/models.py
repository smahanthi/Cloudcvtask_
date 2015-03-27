from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True,  autoincrement=False)
    username = db.Column(db.String(80))
    jobids = db.relationship('jobid', backref='theuser', lazy='dynamic')
    def __init__(self, username, id):
        self.id = id
        self.username = username
    def __repr__(self):
        return '<User %r>' % self.username


class jobid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(8))
    user_id = db.Column(db.Integer,  db.ForeignKey('user.id'))
   
    def __init__(self, user_id,  job_id):
        self.job_id = job_id
        self.user_id = user_id
    def __repr__(self):
        return '<jobid %r>' % self.job_id

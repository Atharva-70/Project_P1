from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
db = SQLAlchemy()
jwt = JWTManager()

def init_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://root:Atharva%40123@localhost:3306/expense_portal_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "SUPER-SECRET-KEY"

    db.init_app(app)
    jwt.init_app(app)
    

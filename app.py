from flask import Flask
from config.database import init_db, db
from controllers.auth_controller import auth_bp
from controllers.expense_category_controller import expense_category_bp
from controllers.travel_controller import travel_bp
from controllers.employee_controller import employee_bp
from controllers.expense_claim_controller import expense_claim_bp
from controllers.expense_item_controller import expense_item_bp
from controllers.expense_receipt_controller import expense_receipt_bp
from controllers.approval_history_controller import approval_history_bp
import models

def create_app():
    app = Flask(__name__)

    init_db(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp)  #Plugs in the routes to the app
    app.register_blueprint(expense_category_bp)
    app.register_blueprint(travel_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(expense_claim_bp)
    app.register_blueprint(expense_item_bp)
    app.register_blueprint(expense_receipt_bp)
    app.register_blueprint(approval_history_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
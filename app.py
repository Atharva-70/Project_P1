import os
from dotenv import load_dotenv
from flask import Flask
from config.database import init_db, db
from controllers.ui_controller import ui_bp
from controllers.auth_controller import auth_bp
from controllers.expense_category_controller import expense_category_bp
from controllers.expense_policy_controller import expense_policy_bp
from controllers.travel_controller import travel_bp
from controllers.employee_controller import employee_bp
from controllers.expense_claim_controller import expense_claim_bp
from controllers.expense_item_controller import expense_item_bp
from controllers.expense_receipt_controller import expense_receipt_bp
from controllers.approval_history_controller import approval_history_bp
from controllers.reimbursement_controller import reimbursement_bp
from controllers.dashboard_controller import dashboard_bp
import models

load_dotenv()


def create_app():
    app = Flask(__name__) 
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me") 

    init_db(app)

    with app.app_context():
        db.create_all()

    # Registering Blueprints for APIs
    app.register_blueprint(ui_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(expense_category_bp)
    app.register_blueprint(expense_policy_bp)
    app.register_blueprint(travel_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(expense_claim_bp)
    app.register_blueprint(expense_item_bp)
    app.register_blueprint(expense_receipt_bp)
    app.register_blueprint(approval_history_bp)
    app.register_blueprint(reimbursement_bp)
    app.register_blueprint(dashboard_bp)

    @app.route("/health", methods=["GET"])
    def health():
        return {"status":"ok"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host = "0.0.0.0",port="5000", debug=True)

#Nothing just for fun
# Testing Jenkins email notification - 3
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


def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = "SUPER-SECRET-KEY"

    init_db(app)

    if test_config:
        app.config.update(test_config)

    with app.app_context():
        db.create_all()

    # Register Web UI routes first
    app.register_blueprint(ui_bp)

    # Register REST API Blueprints
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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
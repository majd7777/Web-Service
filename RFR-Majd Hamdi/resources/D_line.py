from flask.views import MethodView
from flask_smorest import Blueprint
from flask import jsonify
from schemas import DLineInfoResponseSchema

blp = Blueprint("D_line", __name__, url_prefix="/D")

class DLineInfoView(MethodView):
    def get(self):
        response = {
            "message": "Line D is currently undergoing its final testing phase. Service is expected to commence shortly upon successful completion. We appreciate your patience and understanding."
        }

        schema = DLineInfoResponseSchema()
        return jsonify(schema.dump(response)), 200

blp.add_url_rule('/get_information', view_func=DLineInfoView.as_view('get_information'))

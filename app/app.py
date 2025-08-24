import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Get the domain from an environment variable
DOMAIN = os.environ.get("DOMAIN", "idp.example.com")
APPLICATION = os.environ.get("APPLICATION", "tailscale")
issuer_url = f"https://{DOMAIN}/application/o/{APPLICATION}/"

@app.route('/.well-known/webfinger', methods=['GET'])
def webfinger():
    resource = request.args.get('resource')
    if resource and resource.startswith('acct:'):
        # Call the IDP for the exact URL's
        idp_response = requests.get(issuer_url)
        idp_json = idp_response.json()

        if idp_response.status_code == 200:
            response_data = {
                "subject": resource,
                "links": [
                    {
                        "rel": "http://openid.net/specs/connect/1.0/issuer",
                        "href": idp_json['issuer']
                    },
                    {
                        "rel": "authorization_endpoint",
                        "href": idp_json['authorization_endpoint']
                    },
                    {
                        "rel": "token_endpoint",
                        "href": idp_json['token_endpoint']
                    },
                    {
                        "rel": "userinfo_endpoint",
                        "href": idp_json['userinfo_endpoint']
                    },
                    {
                        "rel": "jwks_uri",
                        "href": idp_json['jwks_uri']
                    }
                ]
            }

            return jsonify(response_data), 200
        else:
            return "Internal server error", 500
    else:
        return "Resource not found", 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)

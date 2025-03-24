import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Get the domain from an environment variable
DOMAIN = os.environ.get("DOMAIN", "idp.example.com")
issuer_url = f"https://{DOMAIN}/application/o/tailscale/"

@app.route('/.well-known/webfinger', methods=['GET'])
def webfinger():
    resource = request.args.get('resource')
    if resource and resource.startswith('acct:'):
        response_data = {
            "subject": resource,
            "links": [
                {
                    "rel": "http://openid.net/specs/connect/1.0/issuer",
                    "href": issuer_url
                },
                {
                    "rel": "authorization_endpoint",
                    "href": issuer_url + "oauth2/authorize"
                },
                {
                    "rel": "token_endpoint",
                    "href": issuer_url + "oauth2/token"
                },
                {
                    "rel": "userinfo_endpoint",
                    "href": issuer_url + "userinfo"
                },
                {
                    "rel": "jwks_uri",
                    "href": issuer_url + "jwks"
                }
            ]
        }
        return jsonify(response_data), 200
    else:
        return "Resource not found", 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)

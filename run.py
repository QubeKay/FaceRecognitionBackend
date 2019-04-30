# Run a test server.
from app import app # face recognition app
# from app.demo import app # tutorial app
app.run(host='0.0.0.0', port=8080, debug=True)

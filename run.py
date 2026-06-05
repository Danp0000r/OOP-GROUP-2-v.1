import os
from __init__ import create_app

app = create_app()

if __name__ == "__main__":
    os.environ.setdefault('FLASK_DEBUG', 'false')
    os.environ.setdefault('FLASK_ENV', 'production')
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
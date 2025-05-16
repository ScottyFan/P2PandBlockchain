
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from p2p_network.supernode.api import app

if __name__ == '__main__':
    print("Starting Supernode on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
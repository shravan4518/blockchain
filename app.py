from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from web3 import Web3
import os
from datetime import datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = "secret_key"
CORS(app)

# Blockchain Configuration
ganache_url = "HTTP://127.0.0.1:7545"
contract_address = "0x0fba7fe07A536a00adEdc670b3FD1F4690803672"
contract_abi = [  {
		"inputs": [
			{
				"internalType": "uint256",
				"name": "id",
				"type": "uint256"
			}
		],
		"name": "approveFile",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "id",
				"type": "uint256"
			}
		],
		"name": "FileApproved",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "id",
				"type": "uint256"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "category",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "address",
				"name": "uploader",
				"type": "address"
			}
		],
		"name": "FileUploaded",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "category",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "hash",
				"type": "string"
			}
		],
		"name": "uploadFile",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "admin",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "files",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "id",
				"type": "uint256"
			},
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "category",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "hash",
				"type": "string"
			},
			{
				"internalType": "address",
				"name": "uploader",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			},
			{
				"internalType": "bool",
				"name": "approved",
				"type": "bool"
			},
			{
				"internalType": "uint256",
				"name": "version",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "filesCount",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "id",
				"type": "uint256"
			}
		],
		"name": "getFile",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}] 

web3 = Web3(Web3.HTTPProvider(ganache_url))
contract = web3.eth.contract(address=contract_address, abi=contract_abi)
admin_account = "0x100fc4994f7D3F117F965d6F407d8cd276b87677"

# Database Configuration
DATABASE = 'file_logs.db'

# IPFS Configuration
ipfs_api_url = "http://127.0.0.1:5001/api/v0"

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    metamask_address TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_approved INTEGER DEFAULT 0
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_address TEXT,
                    action TEXT,
                    file_name TEXT,
                    category TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    conn.commit()
    conn.close()

# Helper Functions
def log_action(user_address, action, file_name, category):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO logs (user_address, action, file_name, category) VALUES (?, ?, ?, ?)',
              (user_address, action, file_name, category))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, username, password, metamask_address, is_admin, is_approved FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def upload_to_ipfs(file):
    try:
        files = {'file': file}
        response = requests.post(f"{ipfs_api_url}/add", files=files)
        response.raise_for_status()
        response_data = response.json()
        return response_data["Hash"]
    except requests.RequestException as e:
        raise Exception(f"IPFS upload failed: {e}")


# Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        metamask_address = request.form['metamask_address']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password, metamask_address, is_admin, is_approved) VALUES (?, ?, ?, 0, 0)',
                      (username, password, metamask_address))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()
        return "Signup successful! Waiting for admin approval."
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = get_user(username)

    if user and check_password_hash(user[2], password):
        if user[5] == 0:  # Check if the account is approved
            return "Your account is pending admin approval."
        session['username'] = username
        session['is_admin'] = bool(user[4])
        session['metamask_address'] = user[3]
        return redirect(url_for('admin' if session['is_admin'] else 'faculty'))
    return "Invalid credentials"

@app.route('/admin_login', methods=['POST'])
def admin_login():
    admin_password = request.form['adminpassword']
    correct_password = "Admin"  # Replace with your actual admin password

    if admin_password == correct_password:
        session['is_admin'] = True  # Set session to mark user as admin
        session['username'] = "admin"  # Optional: Set a username for the admin
        return redirect(url_for('admin'))  # Redirect to the admin dashboard
    else:
        # Render the login page with an error message
        return render_template('login.html', error="Invalid admin password")




@app.route('/faculty', methods=['GET', 'POST'])
def faculty():
    if 'username' not in session or session.get('is_admin', False):
        return redirect(url_for('index'))

    if request.method == 'POST':
        file = request.files['file']
        category = request.form['category']
        visibility = request.form.get('visibility', 'Private')  # Default visibility to Private

        try:
            # Upload file to IPFS
            file_hash = upload_to_ipfs(file)
            file_name = file.filename

            # Upload file details to blockchain
            tx_hash = contract.functions.uploadFile(file_name, category, file_hash).transact({
                'from': get_user(session['username'])[3]
            })
            web3.eth.wait_for_transaction_receipt(tx_hash)

            # Log file upload in local database
            log_action(get_user(session['username'])[3], 'Upload', file_name, category)
            return jsonify({"message": "File uploaded successfully!", "ipfs_hash": file_hash})
        except Exception as e:
            return jsonify({"error": str(e)})

    # Render files
    files = []
    try:
        files_count = contract.functions.filesCount().call()
        for i in range(files_count):
            file = contract.functions.getFile(i).call()
            if file[6]:  # Only approved files
                visibility = "Public" if file[6] else "Private"
                files.append({
                    "id": file[0],
                    "name": file[1],
                    "category": file[2],
                    "uploader": file[4],
                    "timestamp": datetime.fromtimestamp(file[5]).strftime('%Y-%m-%d %H:%M:%S'),
                    "approved": file[6],
                    "version": file[7],
                    "visibility": visibility,
                    "ipfs_hash": f"https://ipfs.io/ipfs/{file[3]}"
                })
    except Exception as e:
        return jsonify({"error": str(e)})

    return render_template('faculty.html', files=files)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'username' not in session or not session.get('is_admin', False):
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'file_id' in request.form:
            file_id = int(request.form['file_id'])
            visibility = request.form.get('visibility', 'Private')  # Default to Private

            # Approve the file on the blockchain
            tx_hash = contract.functions.approveFile(file_id).transact({
                'from': admin_account
            })
            web3.eth.wait_for_transaction_receipt(tx_hash)

            # Log approval with visibility
            file_name = contract.functions.getFile(file_id).call()[1]  # Fetch file name from contract
            category = contract.functions.getFile(file_id).call()[2]  # Fetch category from contract
            log_action(admin_account, f"Approved ({visibility})", file_name, category)

            return jsonify({"message": f"File approved as {visibility}!"})

        if 'approve_user' in request.form:
            user_id = int(request.form['approve_user'])
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('UPDATE users SET is_approved = 1 WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return "User approved successfully!"

    # Fetch pending users
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE is_approved = 0')
    pending_users = c.fetchall()
    conn.close()

    # Fetch uploaded files
    files = []
    try:
        files_count = contract.functions.filesCount().call()
        for i in range(files_count):
            file = contract.functions.getFile(i).call()
            visibility = "Public" if file[6] else "Private"
            uploader = file[4]
            c = sqlite3.connect(DATABASE).cursor()
            c.execute("SELECT username FROM users WHERE metamask_address = ?", (uploader,))
            uploader_username = c.fetchone()	
            uploader_username = uploader_username[0] if uploader_username else "Unknown"

            files.append({
                "id": file[0],
                "name": file[1],
                "category": file[2],
                "uploader": file[4],
                "uploader_username": uploader_username,
                "timestamp": datetime.fromtimestamp(file[5]).strftime('%Y-%m-%d %H:%M:%S'),
                "approved": file[6],
                "version": file[7],
                "visibility": visibility,
                "ipfs_hash": file[3]
            })
    except Exception as e:
        return jsonify({"error": str(e)})

    return render_template('admin.html', files=files, pending_users=pending_users)

def update_schema():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Check if the column already exists
    c.execute("PRAGMA table_info(files);")
    columns = [col[1] for col in c.fetchall()]
    if 'visibility' not in columns:
        # Add the 'visibility' column
        c.execute("ALTER TABLE files ADD COLUMN visibility TEXT DEFAULT 'Private';")
        print("Column 'visibility' added to the 'files' table.")
    else:
        print("Column 'visibility' already exists in the 'files' table.")
    
    conn.commit()
    conn.close()
    
if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.mkdir('uploads')
    init_db()
    update_schema()
    app.run(debug=True)
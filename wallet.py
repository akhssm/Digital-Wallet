import socket
import psycopg2
import random
import string
from datetime import datetime

# Database configuration
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "akshay@2002"
DB_HOST = "localhost"
DB_PORT = "5432"

# Dictionary to store active sessions
active_sessions = {}

# Function to generate a secure token
def generate_token(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Handle login request
def handle_login(username, password):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            token = generate_token()
            active_sessions[token] = username
            return True, token
        else:
            return False, None
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return False, None


# Handle login request
def handle_login_request(data):
    try:
        form_data = {}
        for field in data.split("&"):
            try:
                key, value = field.split("=")
                form_data[key] = value
            except ValueError:
                print("Invalid field format:", field)

        username = form_data.get("username", "")
        password = form_data.get("password", "")
        
        success, token = handle_login(username, password)
        if success:
            # Construct JavaScript to redirect to the dashboard page
            redirect_js = f"""
            <script>
                alert("User login Successfull.");
                window.location.href = "/dashboard?token={token}";
            </script>
            """
            return redirect_js
        else:
            # JavaScript alert for invalid username or password
            invalid_alert = """
            <script>
                alert("Invalid username or password. Please try again.");
                window.location.href = "/login";
            </script>
            """
            return invalid_alert
    except Exception as e:
        print("An error occurred:", e)
        return "An error occurred while processing your request."

# Handle registration form
# Handle registration form
def handle_registration_form(data):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        form_data = {}
        for field in data.split("&"):
            try:
                key, value = field.split("=")
                form_data[key] = value
            except ValueError:
                print("Invalid field format:", field)

        username = form_data.get("username", "")
        password = form_data.get("password", "")

        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Construct JavaScript to redirect to the login page
        redirect_js = """
        <script>
            alert("Registration successful! You can now login.");
            window.location.href = "/login";
        </script>
        """
        return redirect_js
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return "An error occurred while processing your request."


# Handle add expense request
# Handle add expense request
def handle_add_expense_request(data, username):
    try:
        # Check if a budget exists for the user
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM travel_budgets WHERE username = %s", (username,))
        existing_budget = cursor.fetchone()

        cursor.close()
        conn.close()

        if existing_budget:
            form_data = {}
            for field in data.split("&"):
                try:
                    key, value = field.split("=")
                    form_data[key] = value
                except ValueError:
                    print("Invalid field format:", field)

            amount = form_data.get("amount", "")
            category = form_data.get("category", "")
            date = form_data.get("date", "")

            # Store the expense details in the database
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            cursor = conn.cursor()

            cursor.execute("INSERT INTO expenses (username, amount, category, date) VALUES (%s, %s, %s, %s)",
                           (username, amount, category, date))
            conn.commit()
            cursor.close()
            conn.close()

            # Construct JavaScript to display an alert message
            alert_message = "Expense added successfully!"
            js_code = f"""
            <script>
                alert("{alert_message}");
                window.location.href = "/dashboard?username={username}";  // Redirect to dashboard after adding expense
            </script>
            """
            return js_code
        else:
            # Return an error message indicating that the user needs to set a budget first
            error_message = "You need to set a budget before adding expenses."
            js_code = f"""
            <script>
                alert("{error_message}");
                window.location.href = "/dashboard?username={username}";  // Redirect to dashboard after displaying error
            </script>
            """
            return js_code
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return "An error occurred while processing your request."

def handle_set_travel_budget(data):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        form_data = {}
        for field in data.split("&"):
            try:
                key, value = field.split("=")
                form_data[key] = value
            except ValueError:
                print("Invalid field format:", field)

        budget_amount = form_data.get("budget_amount", "")
        username = form_data.get("username", "")

        # Check if a budget already exists for the user
        cursor.execute("SELECT * FROM travel_budgets WHERE username = %s", (username,))
        existing_budget = cursor.fetchone()
        if existing_budget:
            # If a budget already exists, return an error message
            return "Budget already set for this user."
        else:
            # If no budget exists, insert the new budget into the database
            cursor.execute("INSERT INTO travel_budgets (username, budget_amount) VALUES (%s, %s)",
                           (username, budget_amount))
            conn.commit()

            # Construct JavaScript to display a success message
            alert_message = "Travel budget set successfully!"
            js_code = f"""
            <script>
                alert("{alert_message}");
                window.location.href = "/dashboard?username={username}";
            </script>
            """
            return js_code

    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return "An error occurred while processing your request."

# Update the handle_request function to handle logout
def handle_request(client_socket, request_data):
    try:
        print("Request data:", request_data)

        request_lines = request_data.split("\r\n")

        if not request_lines:
            print("No request lines found")
            client_socket.close()
            return

        try:
            request_method, request_route, _ = request_lines[0].split()
        except ValueError:
            print("Invalid request format")
            client_socket.close()
            return

        print("Request method:", request_method)
        print("Request route:", request_route)

        # Find the index where the empty line occurs, separating HTTP headers from form data
        empty_line_index = request_data.find("\r\n\r\n")

        if empty_line_index != -1 or request_method == "GET":
            # Handle GET requests differently
            if request_method == "POST":
                form_data = request_data[empty_line_index + 4:]  # Extract form data
                if request_route == "/register":
                    response = handle_registration_form(form_data)
                elif request_route == "/login":
                    response = handle_login_request(form_data)
                elif request_route.startswith("/add_expense"):
                    username = request_route.split("=")[-1]
                    response = handle_add_expense_request(form_data, username)
                elif request_route.startswith("/set_budget"):
                    username = request_route.split("=")[-1]
                    if username:
                        response = handle_set_travel_budget(form_data)
                elif request_route == "/logout":
                    response = handle_logout(form_data)
                else:
                    response = "POST requests not supported yet."
            else:
                if request_route == "/":
                    response = """
    <html>
    <head>
        <title>Welcome</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body {
                background-color: #f3f5f8; /* Updated background color */
            }
            .container {
                margin-top: 50px;
                text-align: center;
            }
            h1 {
                color: #ff0000; /* Red color for header */
            }
            p {
                color: #333; /* Text color */
                font-size: 18px;
            }
            .btn-primary {
                background-color: #228b22; /* Green color for login button */
                border-color: #228b22; /* Green color for login button border */
            }
            .btn-primary:hover {
                background-color: #006400; /* Dark green color for login button hover */
                border-color: #006400; /* Dark green color for login button border hover */
            }
            .btn-secondary {
                background-color: #4169e1; /* Blue color for register button */
                border-color: #4169e1; /* Blue color for register button border */
            }
            .btn-secondary:hover {
                background-color: #0000cd; /* Dark blue color for register button hover */
                border-color: #0000cd; /* Dark blue color for register button border hover */
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="mt-5">Travel Expense Manager</h1>
            <p>Welcome to the Budget Planner!</p>
            <p>Please <a href="/login" class="btn btn-primary">login</a> or <a href="/register" class="btn btn-secondary">register</a>.</p>
        </div>
    </body>
    </html>
"""

                elif request_route == "/login":
                    response = generate_login_form()
                elif request_route == "/register":
                    response = generate_register_form()
                elif request_route.startswith("/dashboard?token"):
                    token = request_route.split("=")[-1]
                    username = active_sessions.get(token)
                    if username:
                        response = generate_dashboard_page(username)
                    else:
                        response = "Invalid token."
                elif request_route.startswith("/dashboard?username"):
                    username = request_route.split("=")[-1]
                    if username:
                        response = generate_dashboard_page(username)
                    else:
                        response = "Invalid token."
                elif request_route.startswith("/set_budget"):
                    username = request_route.split("=")[-1]
                    if username:
                        if request_method == "GET":
                            response = generate_set_budget_form(username)    
                        else:
                            response = "Invalid request method."
                    else:
                        response = "Invalid token."
                elif request_route.startswith("/expense"):
                    username = request_route.split("=")[-1]
                    response = generate_add_expense_form(username)
                
                elif request_route.startswith("/transactions"):
                    username = request_route.split("=")[-1]
                    if username:
                        response = generate_transactions_page(username)
                    else:
                        response = "Invalid token."

                    
                else:
                    response = """
                    <html>
                    <head>
                        <title>Error</title>
                        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
                    </head>
                    <body>
                        <div class="container">
                            <h1 class="mt-5">404 Not Found</h1>
                            <p>The requested page could not be found.</p>
                        </div>
                    </body>
                    </html>
                    """
        else:
            print("Invalid request format")
            client_socket.close()
            return

        print("Response:", response)
        client_socket.sendall(f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{response}".encode())
        client_socket.close()
    except Exception as e:
        print("An error occurred:", e)
        client_socket.close()

def generate_transactions_page(username):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Fetch the budget for the user
        cursor.execute("SELECT budget_amount FROM travel_budgets WHERE username = %s", (username,))
        budget_row = cursor.fetchone()
        budget = budget_row[0] if budget_row else 0

        # Fetch the expenses for the user
        cursor.execute("SELECT amount, category, date FROM expenses WHERE username = %s", (username,))
        expenses = cursor.fetchall()

        # Generate HTML for displaying transactions
        transactions_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transactions</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .container {{
                margin-top: 10px;
                margin-bottom: 10px;
                padding: 5px;
            }}
            .logout-button {{
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h3>Transactions</h3>
            <p>Budget: {budget}</p>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead class="thead-light">
                        <tr>
                            <th>Amount</th>
                            <th>Category</th>
                            <th>Date</th>
                            <th>Balance</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Initialize balance with budget
        balance = budget

        # Calculate balance for each expense and add to the HTML
        for expense in expenses:
            amount = expense[0]
            category = expense[1]
            date = expense[2]

            # Subtract the expense amount from the balance
            balance -= amount

            transactions_html += f"<tr><td>{amount}</td><td>{category}</td><td>{date}</td><td>{balance}</td></tr>"

        transactions_html += """
                        </tbody>
                    </table>
                </div>
                <button onclick="backToDashboard()" class="btn btn-primary btn-sm">Back to Dashboard</button>
                <button onclick="logout()" class="btn btn-danger logout-button btn-sm">Logout</button>
            </div>
            <script>
                function backToDashboard() {
                    window.location.href = '/dashboard?username=""" + username + """';
                }
                function logout() {
                    alert('Successfully logged out.');
                    window.location.href = '/';
                }
            </script>
        </body>
        </html>
        """

        cursor.close()
        conn.close()

        return transactions_html
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return "An error occurred while processing your request."


def generate_set_budget_form(username):
    return f"""
    <html>
    <head>
        <title>Set Travel Budget</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container">
            <h1 class="mt-5">Set Travel Budget</h1>
            <form action="/set_budget?username={username}" method="POST">
                <input type="hidden" name="username" value="{username}">
                <div class="form-group">
                    <label for="budget_amount">Budget Amount:</label>
                    <input type="text" class="form-control" id="budget_amount" name="budget_amount">
                </div>
                <button type="submit" class="btn btn-primary">Set Budget</button>
            </form>
        </div>
    </body>
    </html>
    """

# Generate HTML content for adding expenses form
def generate_add_expense_form(username):
    return f"""
    <html>
    <head>
        <title>Add Expense</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container">
            <h1 class="mt-5">Add Expense</h1>
            <form action="/add_expense?username={username}" method="POST">
                <input type="hidden" name="username" value="{username}">
                <div class="form-group">
                    <label for="amount">Amount:</label>
                    <input type="text" class="form-control" id="amount" name="amount">
                </div>
                <div class="form-group">
                    <label for="category">Category:</label>
                    <input type="text" class="form-control" id="category" name="category">
                </div>
                <div class="form-group">
                    <label for="date">Date:</label>
                    <input type="date" class="form-control" id="date" name="date">
                </div>
                <button type="submit" class="btn btn-primary">Add Expense</button>
            </form>
        </div>
    </body>
    </html>
    """

def generate_login_form():
    return """
    <html>
    <head>
        <title>Login</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body {
                background-color: #eaeaea; /* Updated background color */
            }
            .container {
                margin-top: 100px;
            }
            .card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .card-header {
                background-color: #007bff; /* Updated header background color */
                color: #fff;
                border-radius: 10px 10px 0 0;
            }
            .form-control {
                border-radius: 6px;
            }
            .btn-primary {
                background-color: #007bff; /* Updated button background color */
                border-color: #007bff; /* Updated button border color */
            }
            .btn-primary:hover {
                background-color: #0056b3; /* Updated button hover background color */
                border-color: #0056b3; /* Updated button hover border color */
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="text-center">Login</h3>
                        </div>
                        <div class="card-body">
                            <form action="/login" method="POST">
                                <div class="form-group">
                                    <label for="username">Username:</label>
                                    <input type="text" class="form-control" id="username" name="username">
                                </div>
                                <div class="form-group">
                                    <label for="password">Password:</label>
                                    <input type="password" class="form-control" id="password" name="password">
                                </div>
                                <button type="submit" class="btn btn-primary btn-block">Login</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def generate_register_form():
    return """
    <html>
    <head>
        <title>Register</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body {
                background-color: #eaeaea; /* Updated background color */
            }
            .container {
                margin-top: 100px;
            }
            .card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .card-header {
                background-color: #007bff; /* Updated header background color */
                color: #fff;
                border-radius: 10px 10px 0 0;
            }
            .form-control {
                border-radius: 6px;
            }
            .btn-primary {
                background-color: #007bff; /* Updated button background color */
                border-color: #007bff; /* Updated button border color */
            }
            .btn-primary:hover {
                background-color: #0056b3; /* Updated button hover background color */
                border-color: #0056b3; /* Updated button hover border color */
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="text-center">Register</h3>
                        </div>
                        <div class="card-body">
                            <form action="/register" method="POST">
                                <div class="form-group">
                                    <label for="username">Username:</label>
                                    <input type="text" class="form-control" id="username" name="username">
                                </div>
                                <div class="form-group">
                                    <label for="password">Password:</label>
                                    <input type="password" class="form-control" id="password" name="password">
                                </div>
                                <button type="submit" class="btn btn-primary btn-block">Register</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# Function to handle logout
def handle_logout(data):
    try:
        form_data = {}
        for field in data.split("&"):
            try:
                key, value = field.split("=")
                form_data[key] = value
            except ValueError:
                print("Invalid field format:", field)

        token = form_data.get("token", "")

        if token in active_sessions:
            del active_sessions[token]
            return generate_login_form()  # Redirect to the login page after logout
        else:
            return "Invalid token."
    except Exception as e:
        print("An error occurred:", e)
        return "An error occurred while processing your request."
    
def generate_dashboard_page(username):
    return f"""
    <html>
    <head>
    <title>Dashboard</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body {{
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
        }}
        .container {{
            margin-top: 50px;
            text-align: center;
        }}
        .btn-primary {{
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            transition-duration: 0.4s;
            cursor: pointer;
        }}
        .btn-primary:hover {{
            background-color: #45a049;
        }}
        .btn-secondary {{
            background-color: #008CBA;
            border: none;
            color: white;
            padding: 10px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            transition-duration: 0.4s;
            cursor: pointer;
        }}
        .btn-secondary:hover {{
            background-color: #006CBA;
        }}
        .btn-info {{
            background-color: #f44336;
            border: none;
            color: white;
            padding: 10px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            transition-duration: 0.4s;
            cursor: pointer;
        }}
        .btn-info:hover {{
            background-color: #d32f2f;
        }}
        .logout-button {{
            position: absolute;
            top: 10px;
            right: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logout-button">
            <button onclick="logout()" class="btn btn-danger">Logout</button>
        </div>
        <h1 class="mt-5">Welcome to the Travel Budget Planner, {username}!</h1>
        <button onclick="window.location.href='/expense?username={username}'" class="btn btn-primary">Add Expense</button>
        <button onclick="window.location.href='/set_budget?username={username}'" class="btn btn-secondary">Set Budget</button>
        <button onclick="window.location.href='/transactions?username={username}'" class="btn btn-info">View Transactions</button>
    </div>
    <script>
        function logout() {{
            alert('Successfully logged out.');
            window.location.href = '/';
        }}
    </script>
</body>
</html>
    """
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind(("localhost", 8080))
    server_socket.listen()
    print("Server is listening on http://localhost:8080")

    while True:
        client_socket, _ = server_socket.accept()
        data = client_socket.recv(1024).decode()
        print(data)
        handle_request(client_socket, data)

        client_socket.close()

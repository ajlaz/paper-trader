# Paper Trader Application
This is a paper trading app that allows users to simulate trading stocks without risking real money. Users are able to create their account, view their portfolio, and quote, buy, and sell stocks.

## Routes

### Authentication

#### /auth/login
- __Request Type__: POST
- __Purpose__: Allows a user to login to their account.
- __Request Body__: 
    * username (String): User's username
    * password (String): User's password
- __Response Format__: JSON
    * Success Response Example:
        * code: 200
        * content: {"message": "Login successfully"}
    * Error Response Example:
        * code: 401
        * content: {"message": "Invalid username or password"}
- __Example Request__:
    ```json
    {
        "username": "user123",
        "password": "password"
    }
    ```
- __Example Response__:
    ```json
    {
        "message": "Login successfully"
    }
    ```
#### /auth/create-account
- __Request Type__: POST
- __Purpose__: Allows a new user to create an account.
- __Request Body__: 
    * username (String): Chosen username for the new account
    * password (String): Chosen password for the new account
    * balance (Float, optional): Initial balance for the account (default is 100000.0)
- __Response Format__: JSON
    * Success Response Example:
        * code: 201
        * content: {"message": "User created successfully", "user_id": 1}
    * Error Response Example:
        * code: 400
        * content: {"error": "Username already exists"}
- __Example Request__:
    ```json
    {
        "username": "newuser",
        "password": "newpassword",
        "balance": 50000.0
    }
    ```
- __Example Response__:
    ```json
    {
        "message": "User created successfully",
        "user_id": 1
    }
    ```

#### /auth/change-password
- __Request Type__: PATCH
- __Purpose__: Allows an existing user to change their password.
- __Request Body__: 
    * username (String): User's username
    * old_password (String): User's current password
    * new_password (String): New password to be set
- __Response Format__: JSON
    * Success Response Example:
        * code: 200
        * content: {"message": "Password updated successfully"}
    * Error Response Example:
        * code: 401
        * content: {"error": "Invalid username or password"}
- __Example Request__:
    ```json
    {
        "username":     "user123",
        "old_password": "oldpassword",
        "new_password": "newpassword"
    }
    ```
- __Example Response__:
    ```json
    {
        "message": "Password updated successfully"
    }
    ```


### Stocks

#### /stocks/quote
- __Request Type__: GET
- __Purpose__: Retrieves the current stock quote for a given stock symbol utilizing the AlphaVantage API.
- __Request Parameters__: 
    * stock (String): The stock symbol to retrieve the quote for
- __Response Format__: JSON
    * Success Response Example:
        * code: 200
        * content:
            {
                "01. symbol": "AAPL",
                "02. open": "116.2500",
                "03. high": "116.4000",
                "04. low": "115.5700",
                "05. price": "116.0300",
                "06. volume": "28239269",
                "07. latest trading day": "2020-10-30",
                "08. previous close": "115.3200",
                "09. change": "0.7100",
                "10. change percent": "0.6159%"
            }
    * Error Response Example:
        * code: 400
        * content: {"error": "Invalid stock symbol"}
- __Example Request__:
    ```bash
    curl -X GET "http://localhost:5002/stocks/quote/AAPL"
    ```
- __Example Response__:
    ```json
    {
        "01. symbol": "AAPL",
        "02. open": "116.2500",
        "03. high": "116.4000",
        "04. low": "115.5700",
        "05. price": "116.0300",
        "06. volume": "28239269",
        "07. latest trading day": "2020-10-30",
        "08. previous close": "115.3200",
        "09. change": "0.7100",
        "10. change percent": "0.6159%"
    }
    ```
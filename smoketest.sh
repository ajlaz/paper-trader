#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5002"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
    case $1 in
        --echo-json) ECHO_JSON=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Define color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
    echo "Checking health status..."
    curl -s -X GET "$BASE_URL/health" | grep -q '"status": "ok"'
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Service is healthy.${NC}"
    else
        echo -e "${RED}Health check failed.${NC}"
        exit 1
    fi
}

# Function to check the health of the database
check_db() {
    echo "Checking database status..."
    curl -s -X GET "$BASE_URL/db-check" | grep -q '"status": "ok"'
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database is healthy.${NC}"
    else
        echo -e "${RED}Database health check failed.${NC}"
        exit 1
    fi
}

###############################################
#
# User Management
#
###############################################

create_user(){
        username=$1
        password=$2
        echo "Creating user $username..."
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/auth/create-account" -H "Content-Type: application/json" -d "{\"username\": \"$username\", \"password\": \"$password\"}")
        if [ "$response" -ne 201 ]; then
                echo -e "${RED}User creation failed with status code $response.${NC}"
                exit 1
        fi
        if [ "$ECHO_JSON" = true ]; then
                echo $response
        fi
        echo -e "${GREEN}User created successfully.${NC}"
}

login_user(){
        username=$1
        password=$2
        echo "Logging in user $username..."
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d "{\"username\": \"$username\", \"password\": \"$password\"}")
        if [ "$response" -ne 200 ]; then
                echo -e "${RED}Login failed with status code $response.${NC}"
                exit 1
        fi
        if [ "$ECHO_JSON" = true ]; then
                echo $response
        fi
        echo -e "${GREEN}User logged in successfully.${NC}"
}

change_password(){
        username=$1
        old_password=$2
        new_password=$3
        echo "Changing password for user $username..."
        response=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$BASE_URL/auth/change-password" -H "Content-Type: application/json" -d "{\"username\": \"$username\", \"old_password\": \"$old_password\", \"new_password\": \"$new_password\"}")
        if [ "$response" -ne 200 ]; then
                echo -e "${RED}Password change failed with status code $response.${NC}"
                exit 1
        fi
        if [ "$ECHO_JSON" = true ]; then
                echo $response
        fi
        echo -e "${GREEN}Password changed successfully.${NC}"
}

###############################################
#
# Stock Management
#
###############################################

buy_stock(){
        user_id=$1
        symbol=$2
        quantity=$3
        echo "Buying stock $symbol for user $user_id..."
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/users/$user_id/stocks/buy" -H "Content-Type: application/json" -d "{\"symbol\": \"$symbol\", \"quantity\": $quantity}")
        if [ "$response" -ne 200 ]; then
                echo -e "${RED}Stock purchase failed with status code $response.${NC}"
                exit 1
        fi
        if [ "$ECHO_JSON" = true ]; then
                echo $response
        fi
        echo -e "${GREEN}Stock purchased successfully.${NC}"
}

sell_stock(){
        user_id=$1
        symbol=$2
        quantity=$3
        echo "Selling stock $symbol for user $user_id..."
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/users/$user_id/stocks/sell" -H "Content-Type: application/json" -d "{\"symbol\": \"$symbol\", \"quantity\": $quantity}")
        if [ "$response" -ne 200 ]; then
                echo -e "${RED}Stock sale failed with status code $response.${NC}"
                exit 1
        fi
        if [ "$ECHO_JSON" = true ]; then
                echo $response
        fi
        echo -e "${GREEN}Stock sold successfully.${NC}"
}

get_portfolio(){
        user_id=$1
        echo "Getting portfolio for user $user_id..."
        response=$(curl -s -X GET "$BASE_URL/users/$user_id/stocks/portfolio")
        if [ "$ECHO_JSON" = true ]; then
                echo $response
        fi
        echo -e "${GREEN}Portfolio retrieved successfully.${NC}"
}

# Run the health checks
check_health
check_db

# User management
create_user "testuser" "testpassword"
create_user "testuser2" "testpassword2"
login_user "testuser" "testpassword"
change_password "testuser" "testpassword" "newpassword"
login_user "testuser" "newpassword"

# Stock management
buy_stock 1 "AAPL" 10
sell_stock 1 "AAPL" 5
sell_stock 1 "AAPL" 2
get_portfolio 1
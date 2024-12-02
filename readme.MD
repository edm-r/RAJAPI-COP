# User Authentication and Profile Management API

## Register User

<http://127.0.0.1:8000/auth/register/>

This endpoint is used to register a new user.

### Request Body

- first_name (text): The first name of the user.

- last_name (text): The last name of the user.

- username (text): The username chosen by the user.

- email (text): The email address of the user.

- password (text): The chosen password for the account.

- confirm_password (text): Confirmation of the chosen password.

- role (text): The role of the user.

- phone_number (text): The phone number of the user.

- newsletter_subscription (text): Indicates if the user has subscribed to the newsletter.

### Response

``` json
{
    "message": "User registered successfully!"
}

 ```

The response of this request is a JSON schema defining the structure of the response data.

## User Login

<http://127.0.0.1:8000/auth/token/>

The endpoint `http://127.0.0.1:8000/auth/token/` is a POST request used for obtaining authentication tokens.

### Request Body

The request body should be of type form-data and include the following parameters:

- `username` (type: text) : The username of the user.

- `password` (type: text) : The password of the user.

### Response

The response will have a status code of 200 and a content type of `application/json`. The response body will be in the following JSON schema:

``` json
{
    "type": "object",
    "properties": {
        "refresh": {
            "type": "string"
        },
        "access": {
            "type": "string"
        }
    }
}

 ```

## Password Reset

<http://127.0.0.1:8000/auth/password-reset/>

This endpoint is used to initiate a password reset process by sending a request with the user's email.

### Request Body

- email (text): The email address of the user for whom the password reset is requested.

### Response

The response of this request is a JSON schema that includes the properties and data types of the response object.

``` json
{
    "detail": "Password reset email sent"
}

 ```

http://127.0.0.1:8000/auth/reset-password/`uidb64`/`token`

### Reset Password

This endpoint is used to reset the password.

#### Request Body

- new_password (text) - The new password for the user.

- confirm_password (text) - The confirmation of the new password.

#### Response

The response is in JSON format and has the following schema:

``` json
{
  "type": "object",
  "properties": {
    "detail": {
      "type": "string"
    }
  },
  "required": ["detail"]
}

 ```

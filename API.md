### Generic error response

#### 1. BadRequest

BadRequest is used to indicate that request parameters are missing or do not meet validation criteria. If the request returns a 400 status, the error message should be rendered below the corresponding input field in the form.

**Response Code: 400**
**Response Type: JSON**
**Example Response:**

```json
{
    "err": {
        "email": [
            "not a valid email format"
        ]
    }
}
```

#### 2. Unauthorized

Unauthorized is used to indicate that a user is attempting to access a protected resource without valid credentials. The response provides the reason for the failed authentication. If the request returns a 401 status, the user should be redirected to the login page for re-authentication.

**Response Code: 401**
**Response Type: JSON**
**Example Response:**

```json
{
    "err": "no login information found"
}
```

#### 3. AccessDeclined

The client does not have permission to access the content. If the request returns a 403 status, the user should be immediately redirected to the access denied page.

**Response Code: 403**
**Response Type: JSON**
**Example Response:**

```json
{
    "err": "you are denied to visit this source"
}
```

#### 4. OperationNotAllowed

OperationNotAllowed is used to indicate that the current operation cannot be completed by the user, possibly due to missing dependent data or a locked resource. If the request returns a 405 status, the client should display a popup informing the user that the operation cannot be completed.

**Response Code: 405**
**Response Type: JSON**
**Example Response:**

```json
{
    "err": "this opreation is not allowed"
}
```



#### 1.login
- **Path: /api/auth/login**
- **Method: POST**
- **Content-Type: application/x-www-form-urlencoded**
- **UrlParam**: None
- **Reuqest Body:**
  |name|type|required|
  |:--:|:--:|:--:|
  |user_name|string|true|
  |password|string|true|

- **Successful Response 200**
  ```json
  {
    "message": "success"
  }
  ```

- **After Request Operation**
  - redirect to home page

#### 2.register
- **Path: /api/auth/register**
- **Method: POST**
- **Content-Type: application/x-www-form-urlencoded**
- **UrlParam**: None
- **Reuqest Body:**
  |name|type|required|
  |:--:|:--:|:--:|
  |user_name|string|true|
  |password|string|true|
  |email|string|true|
  |first_name|string|true|
  |last_name|string|true|
  |location|string|true|
  |description|string|true|

- **Successful Response 200**
  ```json
  {
    "message": "success"
  }
  ```

- **After Request Operation**
  - redirect to sign in page

#### 3.logout
- **Path: /api/auth/logout**
- **Method: POST**
- **Content-Type: application/x-www-form-urlencoded**
- **UrlParam**: None
- **Reuqest Body:**: None

- **Successful Response 200**
  ```json
  {
    "message": "success"
  }
  ```

- **After Request Operation**
  - redirect to sign in page


#### 4.current user
- **Path: /api/auth/current**
- **Method: GET**
- **UrlParam**: None

- **Successful Response 200**
  ```json
  {
      "data": {
          "user_id": 1,
          "user_name": "test",
          "user_email": "test@gmail.com",
          "user_fname": "joe",
          "user_lname": "hooe",
          "user_location": "U.S.A.",
          "user_description": "....",
          "user_photo": "",
          "user_role": "admin",
          "user_status": "active"
      }
  }
  ```

#### 5. all events
- **Path: /api/event/list**
- **Method: GET**
- **UrlParam**:
  |name|required|
  |:--:|:--:|
  |journey_id|true|

- **Successful Response 200**
  ```json
  {
    "data": [
      {
        "event_description": "Arrived in Miami and boarded the cruise ship.",
        "event_end_date": null,
        "event_id": 98,
        "event_location": "Miami, USA",
        "event_photo": null,
        "event_start_date": "Sun, 15 Jun 2025 00:00:00 GMT",
        "event_title": "Arrival in Miami",
        "journey_id": 20
      },
      {
        "event_description": "Stopped in the Bahamas and enjoyed the beaches.",
        "event_end_date": "Mon, 16 Jun 2025 00:00:00 GMT",
        "event_id": 99,
        "event_location": "Nassau, Bahamas",
        "event_photo": null,
        "event_start_date": "Mon, 16 Jun 2025 00:00:00 GMT",
        "event_title": "Bahamas Stop",
        "journey_id": 20
      }
    ]
  }
  ```
# 🏀 NBA Database Project - API Documentation (v2.1)

This documentation provides details for the RESTful API developed for the NBA 2023-24 Season Database Project.

The backend is built using **Flask** and **MySQL Connector**. It utilizes **Raw SQL** queries for all database operations (No ORM used), strictly adhering to project constraints.

## 🔗 Base URL
All API requests should be prefixed with:
`http://[SERVER_IP]:5001/api/v1`

* **Local Development:** `http://localhost:5001/api/v1`
* **Production:** Replace `localhost` with the server IP.

---

## 1. 🏃‍♂️ PLAYERS ENDPOINTS

### 📌 List All Players
Retrieves a list of all players in the database.
* **Endpoint:** `/players`
* **Method:** `GET`
* **Query Parameters:** None
* **Response:**
    ```json
    {
      "status": "success",
      "results": 100,
      "data": { "players": [...] }
    }
    ```

### 📌 Get Player Details & Stats
Retrieves detailed information and statistics for a specific player. Supports dynamic filtering by season type and location.
* **Endpoint:** `/players/<id>`
* **Method:** `GET`
* **Query Parameters:**
    * `location`: `OVERALL` (Default - Calculated via Aggregation), `HOME`, `AWAY`
    * `season`: `REGULAR` (Default), `PLAYOFF`
* **Examples:**
    * `GET /players/1631260` (Returns Overall Regular Season Stats)
    * `GET /players/1631260?season=PLAYOFF&location=HOME` (Returns Home Playoff Stats)

### 📌 Search Players
Search for players by name using SQL `LIKE` queries.
* **Endpoint:** `/players/search`
* **Method:** `GET`
* **Query Parameters:**
    * `q`: The name or partial name to search for (e.g., "LeBron").
* **Example:** `GET /players/search?q=Curry`

### 📌 Create Player (Admin)
Adds a new player to the database manually.
* **Endpoint:** `/players`
* **Method:** `POST`
* **Body (JSON):**
    ```json
    {
      "playerName": "New Player Name",
      "teamID": 1610612749,
      "position": "Guard",
      "headshotUrl": "[http://example.com/photo.png](http://example.com/photo.png)"
    }
    ```

### 📌 Update Player (Admin)
Updates specific fields of an existing player.
* **Endpoint:** `/players/<id>`
* **Method:** `PUT`
* **Body (JSON):** (Include only fields to be updated)
    ```json
    {
      "teamID": 1610612750,
      "position": "Center"
    }
    ```

### 📌 Delete Player (Admin)
Deletes a player and cascades the deletion to their statistics in related tables to maintain referential integrity.
* **Endpoint:** `/players/<id>`
* **Method:** `DELETE`

---

## 2. 🏢 TEAMS ENDPOINTS

### 📌 List Teams
Retrieves a list of NBA teams. Supports filtering by conference.
* **Endpoint:** `/teams`
* **Method:** `GET`
* **Query Parameters:**
    * `conference`: `East` or `West`. (Optional. If omitted, returns all teams).
* **Examples:**
    * `GET /teams` (All 30 Teams)
    * `GET /teams?conference=East` (Only Eastern Conference Teams)

---

## 3. 📊 STATISTICS & ANALYTICS

### 📌 Top Performers (Leaders)
Retrieves the top 5 players for a specific statistical category. Uses `ORDER BY` and `JOIN` operations.
* **Endpoint:** `/stats/leaders`
* **Method:** `GET`
* **Query Parameters:**
    * `category`: `PTS` (Points), `AST` (Assists), `REB` (Rebounds), `efficiency`, `STL` (Steals), `BLK_X` (Blocks). (Default: PTS)
    * `season`: `REGULAR` or `PLAYOFF`.
* **Example:** `GET /stats/leaders?category=AST&season=REGULAR`

### 📌 Complex Analysis
Executes a complex SQL query involving joins across 4 tables, nested queries, and grouping.
* **Logic:** Lists teams that have players performing above the league average efficiency, ordered by the count of such "star" players.
* **Endpoint:** `/stats/complex`
* **Method:** `GET`

---

## 🛠 Status Codes

| Code | Description |
| :--- | :--- |
| **200** | Success |
| **201** | Created Successfully |
| **400** | Bad Request (Missing parameters or invalid data) |
| **404** | Not Found (Player or Team does not exist) |
| **500** | Internal Server Error (Database connection issues, etc.) |

---

## ⚙️ Setup & Installation

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Variables:**
    Create a `.env` file and configure your DB credentials (`DB_HOST`, `DB_USER`, `DB_PASSWORD`).
3.  **Run Server:**
    ```bash
    python app.py
    ```
    The server will start on port **5001**.
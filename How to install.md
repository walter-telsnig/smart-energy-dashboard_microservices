# How to Install and Run

## 1. Start the Stack

Open your terminal in the project root:

```bash
docker-compose up -d --build
```

This will start all 5 services + InfluxDB.
Wait about 10-20 seconds for InfluxDB to initialize and the services to connect.

## 2. Register a User

Since the frontend only implements Login, you need to register a user via API first.
You can use **curl** or **Postman**.

**Request:**
`POST http://localhost:8003/register`

**Body (JSON):**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Curl Command:**
```bash
curl -X POST http://localhost:8003/register \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "password123"}'
```

## 3. Access Dashboard

1.  Open your browser to `http://localhost:8050`.
2.  Enter the credentials you just created (`admin` / `password123`).
3.  Click Login.
4.  You should see the dashboard with live updating graphs.

## Troubleshooting

-   **No Data?** Ensure `ingest_service` is running (`docker logs ingest_service`).
-   **Login Failed?** Check `auth_service` logs.
-   **InfluxDB Error?** Ensure InfluxDB is up on port 8086.

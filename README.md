# GreetKart

A Django e-commerce application containerized with Docker.

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Clone the repository:
   ```
   git clone <repository-url>
   cd GreetKart
   ```

2. Build and start the containers:
   ```
   docker-compose up --build
   ```

3. Access the application:
   - Web application: http://localhost:8000

### Docker Commands

- Start the application:
  ```
  docker-compose up
  ```

- Start the application in detached mode:
  ```
  docker-compose up -d
  ```

- Stop the application:
  ```
  docker-compose down
  ```

- View logs:
  ```
  docker-compose logs
  ```

- View logs for a specific service:
  ```
  docker-compose logs web
  ```

- Execute commands in the container:
  ```
  docker-compose exec web python manage.py createsuperuser
  ```

### Environment Variables

The application uses the following environment variables, which are set in the docker-compose.yml file:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `DB_ENGINE`: Database engine
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `EMAIL_*`: Email configuration variables

## Development

For local development without Docker, refer to the project's original setup instructions.

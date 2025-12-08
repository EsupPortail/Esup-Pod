# Windows Development Guide

Welcome! Choose your preferred development setup below.

Note: If you are on Linux or macOS, please refer to the [Linux/macOS Development Guide](dev_unix.md).

## Scenario 1: Windows WITH Docker (Recommended)

This is the **recommended method**. It isolates the database and all dependencies for a clean, reliable setup.

### 1. Prerequisites

- Install **Docker Desktop**.  
- (Optional but recommended) Enable **WSL2**.

### 2. Getting Started

1. **Configuration:**  
   Create a `.env` file in the root of the project (copy the example below).

2. **Start the project:**  
   Open PowerShell or CMD in the `deployment/dev` folder and run:

```powershell
cd deployment/dev
docker-compose up --build -d
```

The `entrypoint.sh` script will automatically:

* Create the database
* Apply migrations
* Create a superuser (`admin/admin`)

### 3. Useful Docker Commands

| Action          | Command (run from `deployment/dev`) |
| --------------- | ----------------------------------- |
| View logs       | `docker-compose logs -f api`        |
| Stop containers | `docker-compose stop`               |
| Full reset      | `docker-compose down -v`            |
| Open shell      | `docker-compose exec api bash`      |


## Scenario 2: Windows WITHOUT Docker (Local Installation)

Use this method **only if Docker cannot be used**. You will need to install MySQL/MariaDB manually.

### 1. Prerequisites

* **Python 3.12+** installed
* MySQL or MariaDB server running on your machine (default port `3306`)

### 2. Installation (PowerShell)

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
pip install -r deployment/dev/requirements.txt
```

### 3. Configuration (.env)

Create a `.env` file in the project root. **Important:** set `MYSQL_HOST` to `localhost`.

### 4. Start the Project

Run the following commands manually each time:

```powershell
# Apply migrations
python manage.py migrate

# Create an admin user (one-time)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The application will be accessible at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## [Go Back](../dev/dev.md)
# PowerShell script to run the Charon web server

# Go to the src/web directory
cd src/web

# Ensure the environment variables are set
$env:CHARON_DB_TYPE = "sqlite"
$env:CHARON_DB_PATH = "../../../data/charon.db"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"

# Start the web server
Write-Host "Starting the Charon web server..."
python server.py 
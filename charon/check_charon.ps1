# PowerShell script to check Charon status

Write-Host "Checking Charon Docker containers..."
docker ps | Select-String "charon"

Write-Host "`nChecking if Charon web interface is available..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 2
    Write-Host "Web interface is available! Status code: $($response.StatusCode)"
    Write-Host "You can access the Charon web interface at http://localhost:5000"
    Write-Host "Login with username: admin, password: admin"
} catch {
    Write-Host "Web interface is not yet available. It might still be starting up."
    Write-Host "You can try accessing it manually at http://localhost:5000"
}

Write-Host "`nChecking if Adminer database interface is available..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8081" -UseBasicParsing -TimeoutSec 2
    Write-Host "Adminer is available! Status code: $($response.StatusCode)"
    Write-Host "You can access the database admin interface at http://localhost:8081"
    Write-Host "Use these credentials to connect to MySQL:"
    Write-Host "System: MySQL"
    Write-Host "Server: mysql-dev"
    Write-Host "Username: charon"
    Write-Host "Password: charonpass"
    Write-Host "Database: charon"
} catch {
    Write-Host "Adminer is not yet available. It might still be starting up."
    Write-Host "You can try accessing it manually at http://localhost:8081"
}

Write-Host "`nTo see logs from the containers, run:"
Write-Host "docker-compose -f docker-compose.dev.yml logs -f" 
# Check if Acronis is already installed
$acronisInstalled = Get-WmiObject -Class Win32_Product | Where-Object { $_.Vendor -like "*Acronis*" }

if ($acronisInstalled) {
    Write-Host "Acronis is already installed. Exiting..."
    exit 0
}

# Check if URL is provided as an argument
if ($args.Count -eq 0) {
    Write-Host "Error: Please provide the download URL as an argument."
    exit 1
}

$URL = $args[0]

# Create Acronis directory
$ACRONIS_DIR = "C:\Acronis"
New-Item -ItemType Directory -Force -Path $ACRONIS_DIR

# Get the filename from the URL
$ARCHIVE = "$ACRONIS_DIR\acronis_installer.zip"
    
# Download the archive
Write-Host "Downloading the archive..."
try {
    Invoke-WebRequest -Uri $URL -OutFile $ARCHIVE
}
catch {
    Write-Host "Error downloading the archive."
    exit 1
}

# Extract the archive
Write-Host "Extracting the archive..."
try {
    Expand-Archive -Path $ARCHIVE -DestinationPath $ACRONIS_DIR -Force
}
catch {
    Write-Host "Error extracting the archive."
    exit 1
}

# Find MSI and MST files
$MSI_FILE = Get-ChildItem -Path $ACRONIS_DIR -Recurse -Filter *.msi | Select-Object -First 1 -ExpandProperty FullName
$MST_FILE = Get-ChildItem -Path $ACRONIS_DIR -Recurse -Filter *.mst | Select-Object -First 1 -ExpandProperty FullName

if (-not $MSI_FILE) {
    Write-Host "Error: MSI file not found in the archive."
    exit 1
}
if (-not $MST_FILE) {
    Write-Host "Error: MST file not found in the archive."
    exit 1
}

# Start the installation
Write-Host "Starting the installation..."
$process = Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$MSI_FILE`" /qn /l*v $ACRONIS_DIR\install.log TRANSFORMS=`"$MST_FILE`"" -Wait -PassThru

if ($process.ExitCode -ne 0) {
    Write-Host "Error during installation."
    exit 1
}

Write-Host "Installation completed successfully."

# Clean up Acronis directory
Remove-Item -Path $ACRONIS_DIR -Recurse -Force
Write-Host "Cleaned up installation files."

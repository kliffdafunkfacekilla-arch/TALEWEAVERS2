$ErrorActionPreference = "Stop"
Set-Location -Path "c:\Users\krazy\Documents\GitHub\TALEWEAVERS\saga_architect"
if (-Not (Test-Path -Path "build")) {
    New-Item -ItemType Directory -Path "build"
}
Set-Location -Path "build"
cmake ..
cmake --build . --config Release

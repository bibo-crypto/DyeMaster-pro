param(
  [string]$Root = (Resolve-Path ".").Path
)

$targets = @(
  Join-Path $Root "__pycache__",
  Join-Path $Root "app\\__pycache__",
  Join-Path $Root "ui\\__pycache__"
)

foreach($t in $targets){
  if(Test-Path $t){
    Remove-Item -Recurse -Force -LiteralPath $t
  }
}

Write-Host "Removed python bytecode caches under: $Root"

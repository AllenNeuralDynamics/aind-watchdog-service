Deployment
-------------


The following script can be used to download and automatically setup the watchdog in a Windows machine:

> [!WARNING]
> Due to restrictive group policies, you may need to run the script with elevated privileges (e.g. as administrator).

```powershell

$url = "https://github.com/AllenNeuralDynamics/aind-watchdog-service/releases/download/0.1.0-rc1/aind-watchdog-service.exe"
$outputPath = Join-Path -Path $env:ProgramData -ChildPath "aind-watchdog-service"
$manifestsPath = Join-Path -Path $outputPath -ChildPath "manifests"
$completedPath = Join-Path -Path $outputPath -ChildPath "completed"

foreach ($path in @($outputPath, $manifestsPath, $completedPath)) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}

$exePath = Join-Path -Path $outputPath -ChildPath "watchdog.exe"
$response = Invoke-WebRequest -Uri $url -OutFile $exePath -TimeoutSec 5
$taskAction = New-ScheduledTaskAction -Execute "$exePath -f $manifestsPath -m $completedPath"
$taskTriggerStartup = New-ScheduledTaskTrigger -AtStartup
$taskTriggerLogOn = New-ScheduledTaskTrigger -AtLogOn
$taskTriggerStartup.Delay = "PT30S"
$taskTriggerLogOn.Delay = "PT30S"
$taskSettings = New-ScheduledTaskSettingsSet -DontStopOnIdleEnd -ExecutionTimeLimit '00:00:00'
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
$taskPath = "AIND"
$taskName = "aind-watchdog-service"
if (Get-ScheduledTask -TaskPath ("\" + $taskPath + "\") -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskPath ("\" + $taskPath + "\") -TaskName $taskName -Confirm:$false
}
$fullTaskPath = "\" + $taskPath + "\" + $taskName
Register-ScheduledTask -TaskName $fullTaskPath -Action $taskAction -Trigger @($taskTriggerStartup, $taskTriggerLogOn) -Settings $taskSettings -Principal $taskPrincipal


```
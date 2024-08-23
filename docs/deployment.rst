Deployment
-------------


The following script can be used to download and automatically setup the watchdog in a Windows machine:

```powershell

$url = "https://github.com/AllenNeuralDynamics/aind-watchdog-service/releases/download/0.1.0-rc1/aind-watchdog-service.exe"
$outputPath = Join-Path -Path $env:APPDATA -ChildPath "aind-watchdog-service"
if (-not (Test-Path -Path $outputPath)) {
    $null = New-Item -Path $outputPath -ItemType Directory
}
$outputPath = Join-Path -Path $outputPath -ChildPath "watchdog.exe"
Invoke-WebRequest -Uri $url -OutFile $outputPath

$taskAction = New-ScheduledTaskAction -Execute "$outputPath"
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
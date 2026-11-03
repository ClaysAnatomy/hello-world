<#
  orient.ps1: read-only, seal-safe orientation for a model joining Project Mystery Machine.
  Prints the live state: git, kit version, agent status, reports, active runs and leftovers.
  It never opens case content (vault, cases, stage folders, bibles, briefs) and never the API token.

  Run:  powershell -ExecutionPolicy Bypass -File "<path>\orient.ps1" [-RunTests]
  Then paste the output to the model, with handoff\MODEL_HANDOFF.md.
#>
param(
  [string]$Root = "D:\Project Recess",
  [switch]$RunTests
)
$ErrorActionPreference = "Continue"
$Proj = Join-Path $Root "Project Mystery Machine"
$Kit  = Join-Path $Proj "authoring_kit"
function H($t) { Write-Host ""; Write-Host "== $t ==" }
function Has($p) { if (Test-Path -LiteralPath $p) { "yes" } else { "no" } }

H "Where"
Write-Host "Git root: $Root   Project: $Proj   Exists: $(Has $Proj)"
Write-Host "Kit source on GitHub: https://github.com/ClaysAnatomy/hello-world (branches claude/eager-davinci-qgiihc = v4, claude/zealous-pasteur-g9zvdz = v4.1)"

H "Git"
Write-Host "Current branch: $(git -C $Root branch --show-current)"
Write-Host "master, last 8:"; git -C $Root log --oneline -8 master
Write-Host "Build branches:"; git -C $Root branch --list "build/*" --format="  %(refname:short) %(objectname:short) %(committerdate:short)"
Write-Host "Tags:"; git -C $Root tag --list "gate-*"
Write-Host "Worktrees:"; git -C $Root worktree list
$dirty = (git -C $Root status --porcelain | Measure-Object).Count
Write-Host "Uncommitted entries in main checkout: $dirty (names not printed)"
$ahead = git -C $Root rev-list --count "master..HEAD" 2>$null
$behind = git -C $Root rev-list --count "HEAD..master" 2>$null
Write-Host "Main checkout vs master: ahead $ahead, behind $behind"

H "Authoring kit"
$v4  = Has (Join-Path $Kit "python\media.py")
$v41 = if (Select-String -Path (Join-Path $Kit "python\kitlib.py") -Pattern "def read_output" -Quiet -ErrorAction SilentlyContinue) { "yes" } else { "no" }
Write-Host "v4 media layer: $v4   v4.1 S1-in-parts: $v41"
Write-Host "Last kit commit:"; git -C $Root log -1 --format="  %h %cd %s" --date=short -- "Project Mystery Machine/authoring_kit"
try {
  $cfg = Get-Content -Raw (Join-Path $Kit "data\kit_config.json") | ConvertFrom-Json
  Write-Host "Agent: family $($cfg.agent.family), model $($cfg.agent.default_model), effort $($cfg.agent.default_effort)"
  Write-Host "Agent argv: $($cfg.agent.argv -join ' ')"
  $lim = Get-Content -Raw (Join-Path $Kit "data\limits.json") | ConvertFrom-Json
  if ($lim.media) { Write-Host "Media caps: items $($lim.media.max_items), plates $($lim.media.max_plates), video max $($lim.media.video.max), exactly-one enforced $($lim.media.video.min_enforced)" }
  Write-Host "Tolerated engine rules: S2 $($lim.tolerated_engine_rules.S2 -join ',')  S3_GATE $($lim.tolerated_engine_rules.S3_GATE -join ',')"
} catch { Write-Host "Could not read kit config: $($_.Exception.Message)" }
Write-Host "Relay settings file present: $(Has (Join-Path $env:USERPROFILE '.mm_secrets\relay_settings.json')) (never open it)"

if ($RunTests) {
  H "Tests (seal-safe output)"
  Push-Location $Proj
  python authoring_kit\tests\run_kit_tests.py | Select-Object -Last 12
  python authoring_kit\python\compat_check.py --root . | Select-Object -Last 3
  Pop-Location
}

H "Agent STATUS (newest, last 15 lines; agent-written and story-free)"
$status = Get-ChildItem (Join-Path $Proj "docs\reports") -Filter "*STATUS*.md" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
if ($status) { Write-Host $status.FullName; Get-Content $status.FullName -Tail 15 } else { Write-Host "none" }

H "Reports (names only, newest 15)"
Get-ChildItem (Join-Path $Proj "docs\reports") -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 15 | ForEach-Object { "  {0:yyyy-MM-dd HH:mm}  {1}" -f $_.LastWriteTime, $_.Name }

H "Handoff folders"
Get-ChildItem (Join-Path $Proj "docs\handoffs") -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object { "  $($_.Name)" }

H "Briefs issued (count only)"
Write-Host "  $((Get-ChildItem (Join-Path $Proj 'taste\data\briefs') -Filter '*.json' -ErrorAction SilentlyContinue | Measure-Object).Count)"

H "Active runs (processes only)"
Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(python|claude|node)' } | Select-Object ProcessName, Id, StartTime, @{n='CPU';e={[math]::Round($_.CPU,1)}} | Format-Table -AutoSize | Out-String | Write-Host

H "Leftover sealed temp folders (counts and dates only; never open)"
foreach ($pat in "mm_kit_stages_*", "pmm_author_*") {
  $d = Get-ChildItem $env:TEMP -Directory -Filter $pat -ErrorAction SilentlyContinue | Sort-Object LastWriteTime
  if ($d) { Write-Host ("  {0}: {1} folders, oldest {2:yyyy-MM-dd HH:mm}, newest {3:yyyy-MM-dd HH:mm}" -f $pat, $d.Count, $d[0].LastWriteTime, $d[-1].LastWriteTime) }
  else { Write-Host "  ${pat}: none" }
}

H "Backups"
Get-ChildItem "H:\Recess\bundles" -Filter "*.bundle" -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object { "  {0}  {1:N0} KB" -f $_.Name, ($_.Length / 1KB) }

H "Read next"
@(
  "1. handoff\MODEL_HANDOFF.md (this repo, or docs\handoffs\ on D:)",
  "2. The STATUS file above, and the newest *build-log*.md in docs\reports",
  "3. authoring_kit\docs\INTEGRATION.md, CRAFT_GUIDE.md, MEDIA.md (open code only to change it)",
  "4. docs\handoffs\2026-11-02_kit-v4\HIGH_INTENSITY_MOMENTS.md",
  "5. Living Log (Google Doc 1c2nQmU117qNUd8vYbTcaaW8b4UxjzAtkPo5RkKcYWEc): newest entries only"
) | ForEach-Object { Write-Host "  $_" }
Write-Host ""
Write-Host "SEAL: never open the vault, cases\, any bible or clue plan, %TEMP%\mm_kit_stages_* or pmm_author_*, or .mm_secrets."

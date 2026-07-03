param(
    [Parameter(Mandatory = $true)]
    [string]$ReviewPath,

    [string[]]$ArtifactPath = @(),

    [string]$RequiredDecision = "pass",

    [switch]$AllowApprovedTextFallback
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ReviewPath)) {
    throw "Claude/NVIDIA review file is missing: $ReviewPath"
}

$text = Get-Content -LiteralPath $ReviewPath -Raw
if ([string]::IsNullOrWhiteSpace($text)) {
    throw "Claude/NVIDIA review file is empty: $ReviewPath"
}

function Get-ReviewDecision {
    param([string]$Text)

    $jsonCandidates = New-Object System.Collections.Generic.List[string]
    foreach ($match in [regex]::Matches($Text, '```json\s*([\s\S]*?)```', 'IgnoreCase')) {
        $jsonCandidates.Add($match.Groups[1].Value)
    }
    $trimmed = $Text.Trim()
    if ($trimmed.StartsWith("{")) {
        $jsonCandidates.Add($trimmed)
    }
    foreach ($match in [regex]::Matches($Text, '(\{[\s\S]*?\})')) {
        $jsonCandidates.Add($match.Groups[1].Value)
    }
    foreach ($candidate in $jsonCandidates) {
        try {
            $obj = $candidate | ConvertFrom-Json
            if ($obj.decision) {
                return ([string]$obj.decision).Trim().ToLowerInvariant()
            }
        } catch {
        }
    }

    $decisionMatch = [regex]::Match($Text, '(?im)["'']?\bdecision\b["'']?\s*[:=]\s*["'']?(pass|block|revise|approved|fail)["'']?')
    if ($decisionMatch.Success) {
        $value = $decisionMatch.Groups[1].Value.ToLowerInvariant()
        if ($value -eq "approved") { return "pass" }
        if ($value -eq "fail") { return "block" }
        return $value
    }

    if ($AllowApprovedTextFallback -and $Text -match '(?i)\bapproved\b|\bpass\b') {
        return "pass"
    }
    return ""
}

$decision = Get-ReviewDecision -Text $text
if (-not $decision) {
    throw "Claude/NVIDIA review does not contain a parseable decision: $ReviewPath"
}
if ($decision -ne $RequiredDecision.ToLowerInvariant()) {
    throw "Claude/NVIDIA review decision is '$decision', expected '$RequiredDecision': $ReviewPath"
}

$missingArtifacts = @()
foreach ($artifact in $ArtifactPath) {
    if ([string]::IsNullOrWhiteSpace($artifact)) { continue }
    $leaf = Split-Path -Leaf $artifact
    if (($text -notlike "*$artifact*") -and ($leaf -and $text -notlike "*$leaf*")) {
        $missingArtifacts += $artifact
    }
}
if ($missingArtifacts.Count -gt 0) {
    throw "Claude/NVIDIA review passed but does not mention required artifact(s): $($missingArtifacts -join '; ')"
}

[pscustomobject]@{
    ok = $true
    review = (Resolve-Path -LiteralPath $ReviewPath).Path
    decision = $decision
    artifact_count = $ArtifactPath.Count
} | ConvertTo-Json -Depth 4

param(
    [Parameter(Mandatory = $true)]
    [string[]]$WorkbookPaths,

    [Parameter(Mandatory = $true)]
    [string]$BadUrl,

    [Parameter(Mandatory = $true)]
    [string]$GoodUrl,

    [string]$Suffix = "_修复OSS截断URL_20260703"
)

$ErrorActionPreference = "Stop"

function New-RepairedPath {
    param([string]$Path, [string]$Suffix)
    $item = Get-Item -LiteralPath $Path
    $dir = $item.DirectoryName
    $name = [System.IO.Path]::GetFileNameWithoutExtension($item.Name)
    $ext = $item.Extension
    return Join-Path $dir ($name + $Suffix + $ext)
}

function Count-In-Workbook {
    param($Workbook, [string]$Needle)
    $count = 0
    $splitPattern = "`r`n|`n|`r|\s+"
    foreach ($sheet in @($Workbook.Worksheets)) {
        $used = $sheet.UsedRange
        $values = $used.Value2
        if ($null -eq $values) { continue }
        if ($values -is [array]) {
            foreach ($value in $values) {
                if ($null -ne $value) {
                    foreach ($token in ([string]$value -split $splitPattern)) {
                        if ($token.Trim() -eq $Needle) {
                            $count++
                        }
                    }
                }
            }
        } else {
            foreach ($token in ([string]$values -split $splitPattern)) {
                if ($token.Trim() -eq $Needle) {
                    $count++
                }
            }
        }
    }
    return $count
}

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

$reports = @()
try {
    foreach ($source in $WorkbookPaths) {
        $sourceItem = Get-Item -LiteralPath $source
        $target = New-RepairedPath -Path $sourceItem.FullName -Suffix $Suffix
        Copy-Item -LiteralPath $sourceItem.FullName -Destination $target -Force

        $workbook = $excel.Workbooks.Open($target)
        try {
            $beforeBad = Count-In-Workbook -Workbook $workbook -Needle $BadUrl
            $beforeGood = Count-In-Workbook -Workbook $workbook -Needle $GoodUrl
            foreach ($sheet in @($workbook.Worksheets)) {
                [void]$sheet.Cells.Replace($BadUrl, $GoodUrl, 2, 1, $false, $false, $false, $false)
            }
            $afterBad = Count-In-Workbook -Workbook $workbook -Needle $BadUrl
            $afterGood = Count-In-Workbook -Workbook $workbook -Needle $GoodUrl
            $workbook.Save()
            $reports += [pscustomobject]@{
                source = $sourceItem.FullName
                output = $target
                before_bad = $beforeBad
                before_good = $beforeGood
                after_bad = $afterBad
                after_good = $afterGood
                changed = ($beforeBad -gt $afterBad)
            }
        } finally {
            $workbook.Close($true)
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
        }
    }
} finally {
    $excel.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
}

$reports | ConvertTo-Json -Depth 4

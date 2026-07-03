param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [switch]$Ensure54Columns,

    [string]$Python = "D:\Programs\Python\Python311\python.exe",

    [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"

$OssHost = "ozonshanghai.oss-cn-shanghai.aliyuncs.com"
$ImageExtPattern = '\.(jpg|jpeg|png|webp)(\?.*)?$'
$UrlPattern = 'https?://[^\s"''<>\]\}]+'

function Get-ImageUrls {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }
    $matches = [regex]::Matches($Text, $UrlPattern)
    $urls = @()
    foreach ($match in $matches) {
        $url = $match.Value.Trim()
        $url = $url.TrimEnd(',', ';')
        if ($url) { $urls += $url }
    }
    return $urls
}

function Test-UrlHead {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 18 -MaximumRedirection 3
        return [pscustomobject]@{
            ok = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
            status = [int]$response.StatusCode
            content_type = [string]$response.Headers['Content-Type']
            content_length = [string]$response.Headers['Content-Length']
            error = ""
        }
    } catch {
        $status = $null
        if ($_.Exception.Response) {
            try { $status = [int]$_.Exception.Response.StatusCode } catch {}
        }
        return [pscustomobject]@{
            ok = $false
            status = $status
            content_type = ""
            content_length = ""
            error = $_.Exception.Message
        }
    }
}

function Get-OssKeyFromUrl {
    param([string]$Url)
    $marker = "https://$OssHost/"
    if (-not $Url.StartsWith($marker)) { return "" }
    $key = $Url.Substring($marker.Length)
    return [System.Uri]::UnescapeDataString($key)
}

function Find-OssRepair {
    param([string]$BadUrl)
    $key = Get-OssKeyFromUrl -Url $BadUrl
    if (-not $key) { return $null }

    $py = @'
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui") / "work"))
import oss2
import generate_apply_ali_tfirst_0608 as ali_t

prefix = sys.argv[1]
cfg = ali_t.ali.read_oss_config()
bucket = oss2.Bucket(oss2.Auth(cfg["access_key_id"], cfg["access_key_secret"]), "https://" + cfg["endpoint"], cfg["bucket"])
found = []
for obj in oss2.ObjectIterator(bucket, prefix=prefix):
    found.append({"key": obj.key, "size": obj.size, "last_modified": obj.last_modified})
    if len(found) >= 20:
        break
print(json.dumps(found, ensure_ascii=False))
'@

    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($py))
    $result = & $Python -c "import base64,sys; exec(base64.b64decode(sys.argv[1]).decode('utf-8'))" $encoded $key
    $objects = $result | ConvertFrom-Json
    if ($null -eq $objects) { return $null }
    if ($objects -isnot [array]) { $objects = @($objects) }

    $candidates = @($objects | Where-Object {
        $_.key -ne $key -and $_.key.StartsWith($key) -and $_.key -match $ImageExtPattern
    })
    if ($candidates.Count -eq 1) {
        return [pscustomobject]@{
            bad_url = $BadUrl
            good_url = "https://$OssHost/$($candidates[0].key)"
            key = $key
            matched_key = $candidates[0].key
            match_count = 1
        }
    }
    return [pscustomobject]@{
        bad_url = $BadUrl
        good_url = ""
        key = $key
        matched_key = ""
        match_count = $candidates.Count
        candidates = $candidates
    }
}

function Resolve-OssUrls {
    param([string[]]$Urls)
    $tmp = [IO.Path]::GetTempFileName()
    try {
        ($Urls | ConvertTo-Json -Depth 3) | Set-Content -LiteralPath $tmp -Encoding UTF8
        $py = @'
import concurrent.futures
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui") / "work"))
import oss2
import generate_apply_ali_tfirst_0608 as ali_t

OSS_HOST = "ozonshanghai.oss-cn-shanghai.aliyuncs.com"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")

with open(sys.argv[2], "r", encoding="utf-8-sig") as handle:
    urls = json.load(handle)

cfg = ali_t.ali.read_oss_config()
bucket = oss2.Bucket(oss2.Auth(cfg["access_key_id"], cfg["access_key_secret"]), "https://" + cfg["endpoint"], cfg["bucket"])

def encode_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(urllib.parse.unquote(parts.path), safe="/%")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))

def head(url: str) -> dict:
    key = key_from_url(url)
    if key:
        try:
            meta = bucket.get_object_meta(key)
            return {
                "ok": True,
                "status": 200,
                "content_type": meta.headers.get("Content-Type", ""),
                "content_length": meta.headers.get("Content-Length", ""),
                "error": "",
                "method": "oss_meta",
            }
        except Exception as exc:
            status = getattr(exc, "status", None)
            return {"ok": False, "status": status, "content_type": "", "content_length": "", "error": str(exc), "method": "oss_meta"}
    try:
        req = urllib.request.Request(encode_url(url), method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=18) as resp:
            return {
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "content_type": resp.headers.get("Content-Type", ""),
                "content_length": resp.headers.get("Content-Length", ""),
                "error": "",
                "method": "http_head",
            }
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "content_type": "", "content_length": "", "error": str(exc), "method": "http_head"}
    except Exception as exc:
        return {"ok": False, "status": None, "content_type": "", "content_length": "", "error": str(exc), "method": "http_head"}

def key_from_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    if parts.netloc != OSS_HOST:
        return ""
    return urllib.parse.unquote(parts.path.lstrip("/"))

def find_repair(url: str) -> dict:
    key = key_from_url(url)
    if not key:
        return {"bad_url": url, "good_url": "", "reason": "not_oss"}
    found = []
    for obj in oss2.ObjectIterator(bucket, prefix=key):
        found.append({"key": obj.key, "size": obj.size, "last_modified": obj.last_modified})
        if len(found) >= 20:
            break
    candidates = [
        obj for obj in found
        if obj["key"] != key and obj["key"].startswith(key) and obj["key"].lower().endswith(IMAGE_EXTS)
    ]
    if len(candidates) != 1:
        return {"bad_url": url, "good_url": "", "reason": "no_unique_oss_repair", "key": key, "match_count": len(candidates), "candidates": candidates}
    good = f"https://{OSS_HOST}/{candidates[0]['key']}"
    good_head = head(good)
    if not good_head.get("ok"):
        return {"bad_url": url, "good_url": "", "reason": "candidate_not_reachable", "key": key, "candidate": candidates[0], "candidate_head": good_head}
    return {"bad_url": url, "good_url": good, "reason": "repaired", "key": key, "matched_key": candidates[0]["key"], "candidate_head": good_head}

def check_one(url: str) -> dict:
    key = key_from_url(url)
    if key and key.lower().endswith(IMAGE_EXTS):
        return {
            "url": url,
            "head": {"ok": True, "status": 200, "content_type": "image/*", "content_length": "", "error": "", "method": "extension_static_check"},
            "ok": True,
            "repair": None,
        }
    h = head(url)
    if h.get("ok") and str(h.get("content_type", "")).startswith("image/"):
        return {"url": url, "head": h, "ok": True, "repair": None}
    repair = find_repair(url)
    return {"url": url, "head": h, "ok": False, "repair": repair}

with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
    results = list(executor.map(check_one, urls))

repairs = []
unresolved = []
for result in results:
    repair = result.get("repair")
    if repair and repair.get("good_url"):
        repairs.append({
            "bad_url": result["url"],
            "good_url": repair["good_url"],
            "status_before": result["head"].get("status"),
            "error_before": result["head"].get("error", ""),
            "status_after": repair["candidate_head"].get("status"),
            "content_type_after": repair["candidate_head"].get("content_type", ""),
        })
    elif not result.get("ok"):
        unresolved.append({"url": result["url"], "head": result["head"], "repair": repair})

print(json.dumps({"checked": len(urls), "repairs": repairs, "unresolved": unresolved}, ensure_ascii=False))
'@
        $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($py))
        $result = & $Python -c "import base64,sys; exec(base64.b64decode(sys.argv[1]).decode('utf-8'))" $encoded $tmp
        return ($result | ConvertFrom-Json)
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}

function Ensure-TemplateColumns {
    param($Worksheet)
    $required = @("SKCID", "SKUID", "创建时间", "更新时间")
    $used = $Worksheet.UsedRange
    $existing = @{}
    for ($c = 1; $c -le $used.Columns.Count; $c++) {
        $header = [string]$Worksheet.Cells.Item(1, $c).Text
        if ($header) { $existing[$header] = $c }
    }
    $col = $used.Columns.Count + 1
    foreach ($header in $required) {
        if (-not $existing.ContainsKey($header)) {
            $Worksheet.Cells.Item(1, $col).Value2 = $header
            $col++
        }
    }
}

function Read-WorkbookUrls {
    param($Workbook)
    $urlCells = @()
    $unique = [ordered]@{}
    foreach ($sheet in @($Workbook.Worksheets)) {
        $used = $sheet.UsedRange
        for ($r = 1; $r -le $used.Rows.Count; $r++) {
            for ($c = 1; $c -le $used.Columns.Count; $c++) {
                $text = [string]$sheet.Cells.Item($r, $c).Value2
                if ([string]::IsNullOrWhiteSpace($text)) { continue }
                $urls = @(Get-ImageUrls -Text $text | Where-Object { $_ -like "https://$OssHost/*" })
                if ($urls.Count -eq 0) { continue }
                foreach ($url in $urls) {
                    if (-not $unique.Contains($url)) { $unique[$url] = $true }
                }
                $urlCells += [pscustomobject]@{ sheet = $sheet.Name; row = $r; col = $c; urls = $urls }
            }
        }
    }
    return [pscustomobject]@{ unique_urls = @($unique.Keys); cells = $urlCells }
}

$source = Get-Item -LiteralPath $SourcePath
$output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
$outputDir = Split-Path -Parent $output
if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

if (Test-Path -LiteralPath $output) {
    Remove-Item -LiteralPath $output -Force
}

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$report = [ordered]@{
    source = $source.FullName
    output = $output
    ensure54Columns = [bool]$Ensure54Columns
    repairs = @()
    unresolved = @()
    validation = @{}
}

try {
    $workbook = $excel.Workbooks.Open($source.FullName)
    try {
        if ($Ensure54Columns) {
            Ensure-TemplateColumns -Worksheet $workbook.Worksheets.Item(1)
        }
        if ([IO.Path]::GetExtension($output).ToLowerInvariant() -eq ".xlsx") {
            $workbook.SaveAs($output, 51)
        } else {
            $workbook.SaveAs($output)
        }
    } finally {
        $workbook.Close($false)
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
    }

    $workbook = $excel.Workbooks.Open($output)
    try {
        $scan = Read-WorkbookUrls -Workbook $workbook
        $repairMap = @{}
        $resolution = Resolve-OssUrls -Urls $scan.unique_urls
        foreach ($repair in @($resolution.repairs)) {
            $repairMap[$repair.bad_url] = $repair.good_url
            $report.repairs += $repair
        }
        foreach ($item in @($resolution.unresolved)) {
            $report.unresolved += $item
        }

        if ($repairMap.Count -gt 0) {
            foreach ($sheet in @($workbook.Worksheets)) {
                $used = $sheet.UsedRange
                for ($r = 1; $r -le $used.Rows.Count; $r++) {
                    for ($c = 1; $c -le $used.Columns.Count; $c++) {
                        $text = [string]$sheet.Cells.Item($r, $c).Value2
                        if ([string]::IsNullOrWhiteSpace($text)) { continue }
                        $newText = $text
                        foreach ($bad in $repairMap.Keys) {
                            if ($newText.Contains($bad)) {
                                $newText = $newText.Replace($bad, $repairMap[$bad])
                            }
                        }
                        if ($newText -ne $text) {
                            $sheet.Cells.Item($r, $c).Value2 = $newText
                        }
                    }
                }
            }
            $workbook.Save()
        }

        $postScan = Read-WorkbookUrls -Workbook $workbook
        $postResolution = Resolve-OssUrls -Urls $postScan.unique_urls
        $badPost = @($postResolution.unresolved)

        $used = $workbook.Worksheets.Item(1).UsedRange
        $headers = @()
        for ($c = 1; $c -le $used.Columns.Count; $c++) {
            $headers += [string]$workbook.Worksheets.Item(1).Cells.Item(1, $c).Text
        }
        $report.validation = [ordered]@{
            sheets = $workbook.Worksheets.Count
            first_sheet_rows = $used.Rows.Count
            first_sheet_cols = $used.Columns.Count
            headers_tail = @($headers | Select-Object -Last 6)
            unique_oss_url_count = $postScan.unique_urls.Count
            bad_post_count = $badPost.Count
            bad_post = $badPost
        }
    } finally {
        $workbook.Close($true)
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
    }
} finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
}

if (-not $ReportPath) {
    $ReportPath = [IO.Path]::ChangeExtension($output, ".oss_url_repair_report.json")
}
$json = $report | ConvertTo-Json -Depth 12
Set-Content -LiteralPath $ReportPath -Value $json -Encoding UTF8
$json

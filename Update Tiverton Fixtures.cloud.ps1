$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $base

$sourceUrl = 'https://www.tivvyarchive.co.uk/season.php?year=2026'
$fwpFixturesUrl = 'https://www.footballwebpages.co.uk/tiverton-town/fixtures-results'
$dataFile = Join-Path $base 'data.json'
$dataJsFile = Join-Path $base 'data.js'
$cacheFile = Join-Path $base 'lineup-cache.json'

function CleanText([string]$s) {
    if ($null -eq $s) { return '' }
    $s = [System.Net.WebUtility]::HtmlDecode($s)
    $s = $s -replace '(?is)<br\s*/?>', ' '
    $s = $s -replace '(?is)<[^>]+>', ' '
    $s = $s -replace '\s+', ' '
    return $s.Trim()
}
function To-IsoDate([string]$s) {
    $culture = [System.Globalization.CultureInfo]::GetCultureInfo('en-GB')
    $raw = $s.Trim()
    foreach($fmt in @('dd/MM/yyyy','dd/MM/yy')) {
        try {
            $dt = [datetime]::ParseExact($raw, $fmt, $culture)
            return $dt.ToString('yyyy-MM-dd')
        } catch { }
    }
    throw "Unrecognised date: $raw"
}
function Get-Page([string]$url, [int]$timeout = 15) {
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($null -ne $curl) {
        for ($attempt=1; $attempt -le 2; $attempt++) {
            $tmp = Join-Path $env:TEMP (('tivvy_' + [guid]::NewGuid().ToString('N')) + '.html')
            $err = Join-Path $env:TEMP (('tivvy_' + [guid]::NewGuid().ToString('N')) + '.err')
            try {
                $args = @('-L','--fail','--silent','--connect-timeout','5','--max-time',[string]$timeout,'-A','Mozilla/5.0','-o',$tmp,$url)
                $proc = Start-Process -FilePath $curl.Source -ArgumentList $args -NoNewWindow -Wait -PassThru -RedirectStandardError $err
                if ($proc.ExitCode -eq 0 -and (Test-Path $tmp)) {
                    $text = [System.IO.File]::ReadAllText($tmp)
                    if (-not [string]::IsNullOrWhiteSpace($text) -and $text -notmatch 'Please wait while your request is being verified') { return $text }
                }
            } catch { }
            finally {
                Remove-Item $tmp -Force -ErrorAction SilentlyContinue
                Remove-Item $err -Force -ErrorAction SilentlyContinue
            }
            Start-Sleep -Milliseconds 150
        }
    }
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -Headers @{'User-Agent'='Mozilla/5.0'} -TimeoutSec $timeout -ErrorAction Stop
        $text = [string]$r.Content
        if ($text -notmatch 'Please wait while your request is being verified') { return $text }
    } catch { }
    return ''
}
function Get-Cells([string]$rowHtml) {
    $list = New-Object System.Collections.Generic.List[string]
    foreach ($cm in [regex]::Matches($rowHtml, '(?is)<t[dh]\b[^>]*>(.*?)</t[dh]>')) { $list.Add((CleanText $cm.Groups[1].Value)) }
    return @($list.ToArray())
}
function Html-ToLines([string]$html) {
    if ([string]::IsNullOrWhiteSpace($html)) { return @() }
    $t = $html
    $t = $t -replace '(?is)<script\b.*?</script>', ''
    $t = $t -replace '(?is)<style\b.*?</style>', ''
    $t = $t -replace '(?is)<br\s*/?>', "`n"
    $t = $t -replace '(?is)</(div|p|li|tr|td|th|h1|h2|h3|h4|section|article|main)>', "`n"
    $t = $t -replace '(?is)<[^>]+>', ''
    $t = [System.Net.WebUtility]::HtmlDecode($t)
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($t -split "`r?`n")) {
        $x = ($line -replace '\s+', ' ').Trim()
        if ($x) { $out.Add($x) }
    }
    return @($out.ToArray())
}
function Is-LikelyPlayerName([string]$s) {
    if ([string]::IsNullOrWhiteSpace($s)) { return $false }
    $x = $s.Trim()
    if ($x.Length -gt 80) { return $false }
    if ($x -match '^(Starting line-?up|Substitutes used|SEASONS|PLAYERS|MANAGERS|OPPONENTS|COMPETITIONS|MISC|Search the Archive|Home|Back|Match Report|Photos|Video|Copyright|About|Useful Links)$') { return $false }
    if ($x -match '^\d{1,2}/\d{1,2}/\d{4}$') { return $false }
    if ($x -match '^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b') { return $false }
    if ($x -match '^(Southern League|FA Cup|FA Trophy|Devon St Luke)\b') { return $false }
    if ($x -match '^Tiverton Town\b.*\d\s*-\s*\d' -or $x -match '\d\s*-\s*\d.*Tiverton Town') { return $false }
    return ($x -match "^[A-Za-z][A-Za-z'.-]+(?:\s+[A-Za-z][A-Za-z'.-]+){1,5}$")
}
function Name-Key([string]$name) {
    if ([string]::IsNullOrWhiteSpace($name)) { return '' }
    $x = $name.ToLowerInvariant()
    $x = $x -replace '\(c\)', ''
    $x = $x -replace '[^a-z -]', ''
    $parts = @($x -split '\s+' | Where-Object { $_ })
    if ($parts.Count -lt 2) { return $x.Trim() }
    return ($parts[0].Substring(0,1) + '|' + $parts[$parts.Count-1])
}
function Get-SquadPageData([int]$id) {
    $url = 'https://www.tivvyarchive.co.uk/squad.php?id=' + $id
    $html = Get-Page $url 10
    if ([string]::IsNullOrWhiteSpace($html)) { return $null }
    $lines = @(Html-ToLines $html)
    if ($lines.Count -eq 0) { return $null }

    $date = ''
    foreach ($line in $lines) {
        $m = [regex]::Match($line, '(?<d>\d{2}/\d{2}/(?:20)?\d{2})')
        if ($m.Success) { try { $date = To-IsoDate $m.Groups['d'].Value } catch { $date = '' }; if ($date) { break } }
    }
    if (-not $date) { return $null }

    $title = ''
    foreach ($line in $lines) { if ($line -match 'Tiverton Town' -and $line -match '\d+\s*-\s*\d+') { $title = $line; break } }
    if (-not $title) { return $null }

    $opponent = ''; $venue=''; $result=''
    $m1 = [regex]::Match($title, '^\s*Tiverton Town\s+(?<tf>\d+)\s*-\s*(?<ta>\d+)\s+(?<opp>.+?)\s*$')
    $m2 = [regex]::Match($title, '^\s*(?<opp>.+?)\s+(?<of>\d+)\s*-\s*(?<oa>\d+)\s+Tiverton Town\s*$')
    if ($m1.Success) {
        $opponent = $m1.Groups['opp'].Value.Trim(); $venue='H'; $result=$m1.Groups['tf'].Value+'-'+$m1.Groups['ta'].Value
    } elseif ($m2.Success) {
        $opponent = $m2.Groups['opp'].Value.Trim(); $venue='A'; $result=$m2.Groups['oa'].Value+'-'+$m2.Groups['of'].Value
    }

    $startIndex=-1; $subsIndex=-1
    for ($i=0; $i -lt $lines.Count; $i++) {
        if ($startIndex -lt 0 -and $lines[$i] -match '^Starting\s+line-?up$') { $startIndex=$i; continue }
        if ($startIndex -ge 0 -and $lines[$i] -match '^Substitutes\s+used$') { $subsIndex=$i; break }
    }
    if ($startIndex -lt 0) { return $null }

    $starters=New-Object System.Collections.Generic.List[string]
    $end = if ($subsIndex -gt $startIndex) { $subsIndex } else { [Math]::Min($lines.Count,$startIndex+14) }
    for ($i=$startIndex+1; $i -lt $end -and $starters.Count -lt 11; $i++) { if (Is-LikelyPlayerName $lines[$i]) { $starters.Add($lines[$i]) } }

    $subs=New-Object System.Collections.Generic.List[string]
    if ($subsIndex -ge 0) {
        for ($i=$subsIndex+1; $i -lt $lines.Count -and $subs.Count -lt 8; $i++) {
            $x=$lines[$i]
            if ($x -match '^(SEASONS|PLAYERS|MANAGERS|OPPONENTS|COMPETITIONS|MISC|Search the Archive|Copyright|About|Useful Links)$') { break }
            if (Is-LikelyPlayerName $x) { $subs.Add($x) }
        }
    }
    if ($starters.Count -lt 11) { return $null }
    return [pscustomobject]@{id=$id;url=$url;date=$date;opponent=$opponent;venue=$venue;result=$result;starters=@($starters.ToArray());subs=@($subs.ToArray())}
}
function Opponent-Slug-Candidates([string]$name) {
    $x = $name.ToLowerInvariant().Trim()
    $x = $x -replace '^sc ', 'sporting club '
    $x = $x -replace '^sporting inkberrow$', 'sporting club inkberrow'
    $x = $x -replace '^shaftsbury$', 'shaftesbury'
    $x = $x -replace '[^a-z0-9]+','-'
    $x = $x.Trim('-')
    $list = New-Object System.Collections.Generic.List[string]
    if ($x) { $list.Add($x) }
    if ($x.EndsWith('-afc')) { $list.Add($x.Substring(0,$x.Length-4)) }
    return @($list.ToArray() | Select-Object -Unique)
}
function Get-FwpMatchLinks([string]$html) {
    $items = New-Object System.Collections.Generic.List[object]
    if ([string]::IsNullOrWhiteSpace($html)) { return @() }
    $rx = '(?is)(?:https?://www\.footballwebpages\.co\.uk)?(?:/tiverton-town)?(?<path>/match/2026-2027/southern-football-league-division-one-south/(?<home>[a-z0-9-]+)/(?<away>[a-z0-9-]+)/(?<id>\d+))'
    foreach ($m in [regex]::Matches($html,$rx)) {
        $items.Add([pscustomobject]@{url=('https://www.footballwebpages.co.uk'+$m.Groups['path'].Value);home=$m.Groups['home'].Value;away=$m.Groups['away'].Value;id=$m.Groups['id'].Value})
    }
    return @($items.ToArray() | Sort-Object url -Unique)
}
function Find-FwpMatchUrl([object[]]$links,[string]$venue,[string]$opponent) {
    $cands = @(Opponent-Slug-Candidates $opponent)
    foreach ($c in $cands) {
        foreach ($l in $links) {
            if ($venue -eq 'H' -and $l.home -eq 'tiverton-town' -and $l.away -eq $c) { return $l.url }
            if ($venue -eq 'A' -and $l.away -eq 'tiverton-town' -and $l.home -eq $c) { return $l.url }
        }
    }
    return ''
}
function Get-FwpMatchData([string]$url) {
    if ([string]::IsNullOrWhiteSpace($url)) { return $null }
    $html = Get-Page $url 15
    if ([string]::IsNullOrWhiteSpace($html)) { return $null }
    $lines = @(Html-ToLines $html)
    if ($lines.Count -eq 0) { return $null }

    $events = New-Object System.Collections.Generic.List[object]
    $goals = New-Object System.Collections.Generic.List[object]
    foreach ($line in $lines) {
        $m = [regex]::Match($line, "^(?<min>\d{1,3}(?:\+\d+)?)'(?<on>.+?)\s+replaced\s+(?<off>.+?)$")
        if ($m.Success) {
            $events.Add([pscustomobject]@{minute=$m.Groups['min'].Value;on=$m.Groups['on'].Value.Trim();off=$m.Groups['off'].Value.Trim()})
            continue
        }
        $gm = [regex]::Match($line, "^(?<min>\d{1,3}(?:\+\d+)?)'(?<scorer>.+?)\s+scores$")
        if ($gm.Success) {
            $goals.Add([pscustomobject]@{minute=$gm.Groups['min'].Value;scorer=$gm.Groups['scorer'].Value.Trim()})
        }
    }

    $best = @()
    for ($i=0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -ne 'Tiverton Town') { continue }
        $cand = New-Object System.Collections.Generic.List[object]
        for ($j=$i+1; $j -lt [Math]::Min($lines.Count,$i+40); $j++) {
            $x=$lines[$j]
            if ($j -gt $i+1 -and $x -match '^(Hungerford Town|Barnstaple Town|Westbury United|Exmouth Town|Dorchester Town|Paulton Rovers|Worcester Raiders|Tiverton Town)$') { break }
            $pm=[regex]::Match($x,'^\s*(?<num>\d{1,2})\s*(?<name>[A-Za-z][A-Za-z .''-]+?)(?<cap>\s*\(C\))?\s*$')
            if ($pm.Success) {
                $nm=($pm.Groups['name'].Value -replace '\s+',' ').Trim()
                if ($nm.Length -ge 4) {$cand.Add([pscustomobject]@{number=[int]$pm.Groups['num'].Value;name=$nm;captain=$pm.Groups['cap'].Success})}
            }
        }
        if ($cand.Count -ge 11 -and $cand.Count -gt $best.Count) { $best=@($cand.ToArray()) }
    }
    if ($best.Count -lt 11) { return [pscustomobject]@{url=$url;players=@();events=@($events.ToArray());goals=@($goals.ToArray())} }
    return [pscustomobject]@{url=$url;players=@($best);events=@($events.ToArray());goals=@($goals.ToArray())}
}

function Get-ScorerKeys([string]$text) {
    $result = @{}
    if ([string]::IsNullOrWhiteSpace($text)) { return $result }
    $clean = $text -replace '\([^)]*\)', ''
    foreach ($part in ($clean -split ',|;|\band\b')) {
        $n = ($part -replace '\s+',' ').Trim()
        if (-not $n) { continue }
        $k = Name-Key $n
        if ($k) {
            if (-not $result.ContainsKey($k)) { $result[$k] = 0 }
            $result[$k]++
        }
    }
    return $result
}
function Get-LastName([string]$name) {
    if ([string]::IsNullOrWhiteSpace($name)) { return '' }
    $parts=@(($name -replace '\(c\)','' -replace '[^A-Za-z'' -]',' ' -replace '\s+',' ').Trim() -split ' ' | Where-Object { $_ })
    if($parts.Count -eq 0){return ''}
    return $parts[$parts.Count-1]
}
function Get-MinuteFromText([string]$text) {
    if([string]::IsNullOrWhiteSpace($text)){return ''}
    $m=[regex]::Match($text,"(?i)\b(?<m>\d{1,3})(?:st|nd|rd|th)?\s*(?:minute|minutes|min|mins)\b")
    if($m.Success){return $m.Groups['m'].Value}
    $m=[regex]::Match($text,"(?i)\b(?:after|on|in|at)\s+(?:the\s+)?(?<m>\d{1,3})(?:st|nd|rd|th)?\b")
    if($m.Success){return $m.Groups['m'].Value}
    return ''
}
function Get-PostLinksFromHtml([string]$html) {
    $links=New-Object System.Collections.Generic.List[string]
    if([string]::IsNullOrWhiteSpace($html)){return @()}
    foreach($m in [regex]::Matches($html,'(?is)href=["''](?<u>(?:https://www\.tivertontownfc\.uk)?/post/[^"''?#]+)')){
        $u=$m.Groups['u'].Value
        if($u.StartsWith('/')){$u='https://www.tivertontownfc.uk'+$u}
        $links.Add($u)
    }
    return @($links.ToArray() | Select-Object -Unique)
}
function Get-TivertonReportCandidates([string]$date,[string]$opponent) {
    $links=New-Object System.Collections.Generic.List[string]
    # Verified 2026/27 match-report URLs. These avoid relying on a site search page.
    $known=@{
        '2026-08-08'='https://www.tivertontownfc.uk/post/hungerford-1-1-tiverton'
        '2026-08-11'='https://www.tivertontownfc.uk/post/slough-s-early-nod-does-the-job'
        '2026-08-15'='https://www.tivertontownfc.uk/post/westbury-united-1-0-tiverton-town'
        '2026-08-31'='https://www.tivertontownfc.uk/post/match-report-tiverton-town-1-2-exmouth-town-slee-blackwell-solicitors-stadium'
        '2026-09-15'='https://www.tivertontownfc.uk/post/defeat-despite-debut-day-delight'
        '2026-09-29'='https://www.tivertontownfc.uk/post/late-drama-in-midweek-devon-vs-somerset-battle'
        '2026-10-03'='https://www.tivertontownfc.uk/post/four-first-half-goals-decides-dramatic-encounter'
    }
    if($known.ContainsKey($date)){$links.Add($known[$date])}

    # Also inspect current club pages for newly published reports. 404s are harmless.
    $q=[uri]::EscapeDataString($opponent)
    $searchLinks=New-Object System.Collections.Generic.List[string]
    foreach($url in @('https://www.tivertontownfc.uk/2025-26-fixtures-results',"https://www.tivertontownfc.uk/search-results?q=$q",'https://www.tivertontownfc.uk/news-blog/categories/first-team','https://www.tivertontownfc.uk/news-blog')){
        $h=Get-Page $url 10
        foreach($u in @(Get-PostLinksFromHtml $h)){
            $links.Add($u)
            if($url -match 'search-results'){$searchLinks.Add($u)}
        }
    }
    $slug=($opponent.ToLowerInvariant() -replace '[^a-z0-9]+','-').Trim('-')
    if($slug){
        $links.Add("https://www.tivertontownfc.uk/post/match-report-$slug")
        $links.Add("https://www.tivertontownfc.uk/post/$slug-match-report")
    }
    $tokens=@($slug -split '-' | Where-Object {$_.Length -ge 4 -and $_ -notin @('town','united','rovers')})
    $scored=@()
    foreach($u in @($links.ToArray() | Select-Object -Unique)){
        $score=0; $lu=$u.ToLowerInvariant()
        if($known.ContainsKey($date) -and $u -eq $known[$date]){$score+=100}
        if($lu -match 'match-report'){$score+=5}
        if($searchLinks.Contains($u)){$score+=8}
        foreach($t in $tokens){if($lu.Contains($t)){$score+=3}}
        if($score -gt 0){$scored += [pscustomobject]@{url=$u;score=$score}}
    }
    return @($scored | Sort-Object score -Descending | Select-Object -First 15 -ExpandProperty url)
}
function Find-ReportPlayer([string]$token,[string[]]$allNames) {
    if([string]::IsNullOrWhiteSpace($token)){return ''}
    $base=($token -replace '\([^)]*\)','' -replace '[^A-Za-z. ''-]',' ' -replace '\s+',' ').Trim()
    if(-not $base){return ''}
    $base2=$base -replace '\.',' '
    $parts=@($base2 -split '\s+' | Where-Object {$_})
    if($parts.Count -eq 0){return ''}
    $last=$parts[$parts.Count-1]
    $firstInitial=''
    if($parts.Count -ge 2){$firstInitial=$parts[0].Substring(0,1)}
    $matches=@()
    foreach($n in $allNames){
        $np=@(($n -replace '[^A-Za-z'' -]',' ' -replace '\s+',' ').Trim() -split '\s+' | Where-Object {$_})
        if($np.Count -eq 0){continue}
        if($np[$np.Count-1] -ieq $last){$matches += $n}
    }
    if($matches.Count -eq 1){return [string]$matches[0]}
    if($firstInitial){
        foreach($n in $matches){
            $t=($n -replace '^\s+|\s+$','')
            if($t.Length -gt 0 -and $t.Substring(0,1) -ieq $firstInitial){return [string]$n}
        }
    }
    return ''
}
function Resolve-ReportPlayerToken([string]$token,[string[]]$allNames) {
    $found=Find-ReportPlayer $token $allNames
    if($found){return $found}
    if([string]::IsNullOrWhiteSpace($token)){return ''}
    $base=($token -replace '\([^)]*\)','' -replace '[^A-Za-z. ''-]',' ' -replace '\s+',' ').Trim()
    if(-not $base){return ''}
    $base=$base -replace '\.',' '
    $parts=@($base -split '\s+' | Where-Object {$_})
    if($parts.Count -eq 0){return ''}
    $last=$parts[$parts.Count-1].ToLowerInvariant()
    $known=@{
        'smith'='Louis Smith'; 'winter'='Mason Winter'; 'palmer'='Ed Palmer'; 'slough'='Louis Slough'
        'koerner'='Corey Koerner'; 'hall'='Asa Hall'; 'wellington'=''; 'keates'='Ryan Keates'
        'roberts'='Finn Roberts'; 'bissett'='Josh Bissett'; 'howe'='Owen Howe'; 'horne'='Aiden Horne'
        'tucker'='Billy Tucker'; 'kennell'='Jack Kennell'; 'wood'='Matt Wood'; 'pryce-hall'='Caleb Pryce-Hall'
        'coulbaly'='Karim Coulibaly'; 'coulibaly'='Karim Coulibaly'; 'koita'='Dan Koita'
    }
    if($last -eq 'wellington'){
        if($base -match '(?i)^A(?:aron)?\s+Wellington$'){return 'Aaron Wellington'}
        if($base -match '(?i)^J(?:acob)?\s+Wellington$'){return 'Jacob Wellington'}
        return ''
    }
    if($base -match '(?i)Pryce\s*-?\s*Hall'){return 'Caleb Pryce-Hall'}
    if($known.ContainsKey($last) -and $known[$last]){return [string]$known[$last]}
    return ''
}

function Get-TivertonReportData([string]$date,[string]$opponent,[string[]]$starters,[string[]]$subs,[hashtable]$scorerKeys) {
    $best=$null; $bestScore=-1
    $dt=[datetime]::ParseExact($date,'yyyy-MM-dd',[Globalization.CultureInfo]::InvariantCulture)
    $datePhrases=@($dt.ToString('MMMM d',[Globalization.CultureInfo]::GetCultureInfo('en-GB')),$dt.ToString('d MMMM',[Globalization.CultureInfo]::GetCultureInfo('en-GB')),$dt.ToString('dd/MM/yyyy'))
    foreach($url in @(Get-TivertonReportCandidates $date $opponent)){
        $html=Get-Page $url 12
        if([string]::IsNullOrWhiteSpace($html)){continue}
        $lines=@(Html-ToLines $html); if($lines.Count -eq 0){continue}
        $text=($lines -join ' '); $lt=$text.ToLowerInvariant(); $score=0
        if($lt.Contains($opponent.ToLowerInvariant())){$score+=6}
        foreach($dp in $datePhrases){if($lt.Contains($dp.ToLowerInvariant())){$score+=8}}
        if($lt.Contains('2026')){$score+=2}
        if($lt -match 'match report'){$score+=3}
        # A Tiverton team line is the strongest signal that this is the actual report.
        if($text -match '(?i)\bTiverton(?: Town)?\s*:'){$score+=12}
        if($score -gt $bestScore){$bestScore=$score;$best=[pscustomobject]@{url=$url;text=$text;lines=$lines}}
    }
    if($null -eq $best -or $bestScore -lt 7){return $null}

    $all=@($starters)+@($subs)
    $captainKey=''; $onMap=@{}; $offMap=@{}; $goalMap=@{}; $reportSubs=New-Object System.Collections.Generic.List[string]

    # Preferred source: the compact team sheet printed at the end of official reports, e.g.
    # Tiverton: Smith(GK), Winter, Palmer(C), ... Horne(55), Jagger Cane(80)
    # Subs: Keates(55), Kennell(69), Tucker(76), Howe(80), Pryce-Hall
    foreach($line in $best.lines){
        $tm=[regex]::Match($line,'(?i)^\s*Tiverton(?: Town)?\s*:\s*(?<list>.+)$')
        if($tm.Success){
            foreach($token in ($tm.Groups['list'].Value -split ',')){
                $token=$token.Trim(); if(-not $token){continue}
                $full=Resolve-ReportPlayerToken $token $all; if(-not $full){continue}
                $k=Name-Key $full
                if($token -match '(?i)\(\s*C\s*\)'){$captainKey=$k}
                $mm=[regex]::Match($token,'\(\s*(?<m>\d{1,3})\s*\)')
                if($mm.Success -and -not $offMap.ContainsKey($k)){$offMap[$k]=$mm.Groups['m'].Value}
            }
        }
        $sm=[regex]::Match($line,'(?i)^\s*Subs?\s*:\s*(?<list>.+)$')
        if($sm.Success){
            foreach($token in ($sm.Groups['list'].Value -split ',')){
                $token=$token.Trim(); if(-not $token){continue}
                $full=Resolve-ReportPlayerToken $token $all; if(-not $full){continue}
                $k=Name-Key $full
                if($k -and -not @($reportSubs | Where-Object {(Name-Key $_) -eq $k}).Count){$reportSubs.Add($full)}
                $mm=[regex]::Match($token,'\(\s*(?<m>\d{1,3})\s*\)')
                if($mm.Success -and -not $onMap.ContainsKey($k)){$onMap[$k]=$mm.Groups['m'].Value}
            }
        }
    }

    # Narrative fallback for reports whose team sheet omits or formats a substitution differently.
    $sentences=@($best.text -split '(?<=[.!?])\s+')
    foreach($sub in $subs){
        $sl=Get-LastName $sub; if(-not $sl){continue}
        foreach($st in $starters){
            $tl=Get-LastName $st; if(-not $tl){continue}
            foreach($sentence in $sentences){
                if($sentence -notmatch ('(?i)\b'+[regex]::Escape($sl)+'\b') -or $sentence -notmatch ('(?i)\b'+[regex]::Escape($tl)+'\b')){continue}
                if($sentence -notmatch '(?i)replac|came on|introduced|substitut|made way'){continue}
                $min=Get-MinuteFromText $sentence; if(-not $min){continue}
                $sk=Name-Key $sub; $tk=Name-Key $st
                if($sk -and -not $onMap.ContainsKey($sk)){$onMap[$sk]=$min}
                if($tk -and -not $offMap.ContainsKey($tk)){$offMap[$tk]=$min}
                break
            }
        }
    }

    # Goal minutes: use only compact score-summary lines such as "Jagger Cane 23".
    # Do NOT infer goals from narrative sentences merely because they mention a scorer and a minute;
    # that previously turned ordinary match events into phantom goals.
    foreach($line in $best.lines){
        $cleanLine=($line -replace '\s+',' ').Trim()
        if(-not $cleanLine -or $cleanLine.Length -gt 90){continue}
        $gm=[regex]::Match($cleanLine,"^(?<who>[A-Za-z][A-Za-z .'-]{1,55}?)\s+(?<mins>\d{1,3}(?:\+\d{1,2})?(?:\s*,\s*\d{1,3}(?:\+\d{1,2})?)*)\s*(?:\(pen\)|pen)?$")
        if(-not $gm.Success){continue}
        $who=$gm.Groups['who'].Value.Trim()
        $full=Find-ReportPlayer $who $all
        if(-not $full){continue}
        $k=Name-Key $full
        if(-not $scorerKeys.ContainsKey($k)){continue}
        if(-not $goalMap.ContainsKey($k)){$goalMap[$k]=New-Object System.Collections.Generic.List[string]}
        foreach($rawMin in ($gm.Groups['mins'].Value -split ',')){
            $min=$rawMin.Trim()
            if($min -and -not $goalMap[$k].Contains([string]$min)){$goalMap[$k].Add([string]$min)}
        }
    }
    # Verified goal-minute fallbacks for reports that describe goals in narrative prose rather than a compact scorer line.
    # These are taken from the published match reports / match records and prevent missed second goals.
    $verifiedGoals=@{
        '2026-09-29'=@(
            [pscustomobject]@{name='Owen Howe';minute='36'},
            [pscustomobject]@{name='Finn Roberts';minute='64'}
        )
        '2026-10-03'=@(
            [pscustomobject]@{name='Aiden Horne';minute='25'},
            [pscustomobject]@{name='Finn Roberts';minute='38'}
        )
    }
    if($verifiedGoals.ContainsKey($date)){
        foreach($vg in @($verifiedGoals[$date])){
            $vk=Name-Key ([string]$vg.name)
            if(-not $goalMap.ContainsKey($vk)){$goalMap[$vk]=New-Object System.Collections.Generic.List[string]}
            $vm=[string]$vg.minute
            if(-not $goalMap[$vk].Contains($vm)){$goalMap[$vk].Add($vm)}
        }
    }

    return [pscustomobject]@{url=$best.url;captainKey=$captainKey;onMap=$onMap;offMap=$offMap;goalMap=$goalMap;reportSubs=@($reportSubs.ToArray())}
}
function Apply-OfficialReportData([object[]]$details,[object]$official) {
    if($null -eq $official){return}
    foreach($pd in @($details)){
        $k=Name-Key $pd.name
        if($official.captainKey -and $k -eq $official.captainKey){$pd.captain=$true}
        if($official.onMap.ContainsKey($k)){$pd.onMinute=[string]$official.onMap[$k];$pd.used=$true}
        if($official.offMap.ContainsKey($k)){$pd.offMinute=[string]$official.offMap[$k]}
        if($official.goalMap.ContainsKey($k)){
            # Official/verified report goal minutes take precedence over secondary sources.
            $mins=@($official.goalMap[$k].ToArray());$pd.goalMinutes=$mins;$pd.goalCount=$mins.Count
        }
    }
}

function Build-PlayerDetails([string[]]$ordered,[object]$fwp,[bool]$isSub,[string]$date,[hashtable]$scorerKeys) {
    $result=New-Object System.Collections.Generic.List[object]
    $playerMap=@{}
    if($null -ne $fwp -and $fwp.players){foreach($p in @($fwp.players)){$k=Name-Key $p.name;if($k){$playerMap[$k]=$p}}}
    $onMap=@{};$offMap=@{};$goalMap=@{}
    if($null -ne $fwp -and $fwp.events){foreach($e in @($fwp.events)){$ok=Name-Key $e.on;$fk=Name-Key $e.off;if($ok){$onMap[$ok]=$e.minute};if($fk){$offMap[$fk]=$e.minute}}}
    if($null -ne $fwp -and $fwp.goals){
        foreach($g in @($fwp.goals)){
            $gk=Name-Key $g.scorer
            if($gk){
                if(-not $goalMap.ContainsKey($gk)){$goalMap[$gk]=New-Object System.Collections.Generic.List[string]}
                $goalMap[$gk].Add([string]$g.minute)
            }
        }
    }
    foreach($name in @($ordered)){
        $k=Name-Key $name;$num=$null;$cap=$false;$on='';$off='';$displayName=$name;$goalMinutes=@()
        if($playerMap.ContainsKey($k)){
            $num=$playerMap[$k].number;$cap=[bool]$playerMap[$k].captain
            # Keep the concise Tivvy Archive name for display (e.g. Ed Palmer, Aiden Horne).
            # Football Web Pages often includes middle names which are not needed here.
        }
        if($onMap.ContainsKey($k)){$on=[string]$onMap[$k]}
        if($offMap.ContainsKey($k)){$off=[string]$offMap[$k]}
        if($goalMap.ContainsKey($k)){$goalMinutes=@($goalMap[$k].ToArray())}
        # Tivvy Archive goalscorers are a reliable fallback even when event pages are unavailable.
        if($goalMinutes.Count -eq 0 -and $scorerKeys.ContainsKey($k)){
            $gc=[int]$scorerKeys[$k]
            $goalMinutes=@()
        } else { $gc=$goalMinutes.Count }
        $used = ((-not $isSub) -or [bool]$on)
        $result.Add([pscustomobject]@{name=$displayName;number=$num;captain=$cap;onMinute=$on;offMinute=$off;goalCount=$gc;goalMinutes=$goalMinutes;sub=$isSub;used=$used})
    }
    return @($result.ToArray())
}

Write-Host ''
Write-Host 'Tiverton Town 2026/27 SL1 fixtures - updating...' -ForegroundColor Yellow
Write-Host 'Fixtures + ordered line-ups: Tivvy Archive' -ForegroundColor Cyan
Write-Host 'Events: TivertonTownFC.uk official match reports + Football Web Pages' -ForegroundColor Cyan

$html = Get-Page $sourceUrl 25
if ([string]::IsNullOrWhiteSpace($html)) { Write-Host 'Could not download the Tivvy Archive season page.' -ForegroundColor Red; exit 1 }

$fixtures = New-Object System.Collections.Generic.List[object]
foreach ($rm in [regex]::Matches($html, '(?is)<tr\b[^>]*>(.*?)</tr>')) {
    $cells=@(Get-Cells $rm.Groups[1].Value)
    if ($cells.Count -lt 5) { continue }
    $dateIndex=-1
    for ($i=0;$i -lt $cells.Count;$i++) { if ($cells[$i] -match '^\d{2}/\d{2}/(?:20)?\d{2}$') { $dateIndex=$i; break } }
    if ($dateIndex -lt 0) { continue }
    try{$iso=To-IsoDate $cells[$dateIndex]}catch{continue}

    $compIndex=-1; $venueIndex=-1
    for($i=$dateIndex+1;$i -lt $cells.Count;$i++){
        $v=$cells[$i].Trim()
        if($compIndex -lt 0 -and $v.ToUpperInvariant() -eq 'SL1'){$compIndex=$i}
        if($venueIndex -lt 0 -and $v.ToUpperInvariant() -match '^[HA]$'){$venueIndex=$i}
    }
    if($compIndex -lt 0 -or $venueIndex -lt 0){continue}
    $venue=$cells[$venueIndex].Trim().ToUpperInvariant()

    $opponent=''; $oppIndex=-1
    for($i=$dateIndex+1;$i -lt $cells.Count;$i++){
        if($i -eq $compIndex -or $i -eq $venueIndex){continue}
        $v=$cells[$i].Trim()
        if(-not $v){continue}
        if($v -match '^\d+$' -or $v -match '^\d+\s*[-–]\s*\d+$'){continue}
        if($v -match '^(SL1|H|A)$'){continue}
        $opponent=$v; $oppIndex=$i; break
    }
    if(-not $opponent){continue}
    $opponent=$opponent -replace '^SC Inkberrow$','Sporting Inkberrow' -replace '^Shaftsbury$','Shaftesbury'

    $result=''; $scoreIndexes=New-Object System.Collections.Generic.List[int]
    for($i=$oppIndex+1;$i -lt $cells.Count;$i++){
        $v=$cells[$i].Trim()
        $m=[regex]::Match($v,'^(?<a>\d+)\s*[-–]\s*(?<b>\d+)$')
        if($m.Success){$result=$m.Groups['a'].Value+'-'+$m.Groups['b'].Value;$scoreIndexes.Add($i);break}
    }
    if(-not $result){
        $nums=New-Object System.Collections.Generic.List[object]
        for($i=$oppIndex+1;$i -lt $cells.Count;$i++){
            $v=$cells[$i].Trim()
            if($v -match '^\d+$'){$nums.Add([pscustomobject]@{idx=$i;v=$v}); if($nums.Count -eq 2){break}}
            elseif($nums.Count -gt 0){break}
        }
        if($nums.Count -eq 2){$result=$nums[0].v+'-'+$nums[1].v;$scoreIndexes.Add([int]$nums[0].idx);$scoreIndexes.Add([int]$nums[1].idx)}
    }
    if(-not $result){continue}

    $goalscorerParts=New-Object System.Collections.Generic.List[string]
    $afterScore=if($scoreIndexes.Count){($scoreIndexes | Measure-Object -Maximum).Maximum}else{$oppIndex}
    for($i=[int]$afterScore+1;$i -lt $cells.Count;$i++){
        $v=$cells[$i].Trim()
        if(-not $v -or $v -match '^\d+$' -or $v -match '^(Report|Photos?|Video)$'){continue}
        $goalscorerParts.Add($v)
    }
    $goalscorers=($goalscorerParts.ToArray() -join ' ').Trim()
    $fixtures.Add([pscustomobject]@{date=$iso;venue=$venue;opponent=$opponent;result=$result;goalscorers=$goalscorers})
}
$unique=@{}; foreach($f in $fixtures){$unique["$($f.date)|$($f.venue)|$($f.opponent)"]=$f}
$sorted=@($unique.Values | Sort-Object date)
if($sorted.Count -eq 0){Write-Host 'No SL1 rows were found.' -ForegroundColor Red; exit 2}
Write-Host ("Found {0} SL1 matches." -f $sorted.Count) -ForegroundColor Green

$knownIds = @{
 '2026-08-08'=4464
 '2026-08-11'=4465
 '2026-08-15'=4466
 '2026-08-31'=4469
 '2026-09-15'=4472
 '2026-09-29'=4476
 '2026-10-03'=4477
}

$knownLeagueFallback=@{
 '2026-09-29'=[pscustomobject]@{id=4476;venue='H';opponent='Paulton Rovers'}
 '2026-10-03'=[pscustomobject]@{id=4477;venue='H';opponent='Worcester Raiders'}
}
foreach($d in $knownLeagueFallback.Keys){
    if(-not @($sorted | Where-Object {$_.date -eq $d}).Count){
        $kf=$knownLeagueFallback[$d]
        $pg=Get-SquadPageData ([int]$kf.id)
        if($null -ne $pg -and $pg.result){
            $rec=[pscustomobject]@{date=$d;venue=$kf.venue;opponent=$kf.opponent;result=$pg.result;goalscorers=''}
            $fixtures.Add($rec); $unique["$d|$($kf.venue)|$($kf.opponent)"]=$rec
            $sorted=@($unique.Values | Sort-Object date)
            Write-Host ("Recovered missing league fixture from Tivvy squad page: {0} {1} {2}" -f $d,$kf.opponent,$pg.result) -ForegroundColor Green
        }
    }
}

$cache=[ordered]@{maxId=4477;matches=[ordered]@{}}
if(Test-Path $cacheFile){
    try{$c=Get-Content $cacheFile -Raw | ConvertFrom-Json; if($c.maxId){$cache.maxId=[int]$c.maxId}; if($c.matches){foreach($p in $c.matches.PSObject.Properties){$cache.matches[$p.Name]=$p.Value}}}catch{}
}
foreach($f in $sorted){
    if($knownIds.ContainsKey($f.date)){
        $id=[int]$knownIds[$f.date]
        $page=Get-SquadPageData $id
        if($null -ne $page){$cache.matches[$f.date]=$page; if($id -gt $cache.maxId){$cache.maxId=$id}}
    }
}
$missing=@($sorted | Where-Object {-not $cache.matches.Contains($_.date)})
if($missing.Count -gt 0){
    Write-Host ("Locating Tivvy squad pages for {0} new/missing match(es)..." -f $missing.Count) -ForegroundColor Cyan
    $start=[Math]::Max(4478,[int]$cache.maxId+1); $end=$start+60
    for($id=$start;$id -le $end;$id++){
        $page=Get-SquadPageData $id
        if($id -gt $cache.maxId){$cache.maxId=$id}
        if($null -ne $page){foreach($f in $sorted){if($f.date -eq $page.date -and -not $cache.matches.Contains($f.date)){$cache.matches[$f.date]=$page;Write-Host ("  Found ordered line-up for {0} [squad {1}]" -f $page.date,$id) -ForegroundColor Green}}}
        if(@($sorted | Where-Object {-not $cache.matches.Contains($_.date)}).Count -eq 0){break}
    }
}
$cache | ConvertTo-Json -Depth 8 | Set-Content $cacheFile -Encoding UTF8

$fwpIndexHtml=Get-Page $fwpFixturesUrl 20
$fwpLinks=@(Get-FwpMatchLinks $fwpIndexHtml)
if($fwpLinks.Count -gt 0){Write-Host ("Found {0} Football Web Pages match links for enrichment." -f $fwpLinks.Count) -ForegroundColor DarkGray}else{Write-Host 'Football Web Pages enrichment index was unavailable; line-ups will still display.' -ForegroundColor Yellow}

$knownFwpMatchUrls=@{
 '2026-09-29'='https://www.footballwebpages.co.uk/match/2026-2027/southern-football-league-division-one-south/tiverton-town/paulton-rovers/583507'
 '2026-10-03'='https://www.footballwebpages.co.uk/match/2026-2027/southern-football-league-division-one-south/tiverton-town/worcester-raiders/583556'
}

$final=New-Object System.Collections.Generic.List[object]
foreach($f in $sorted){
    $starters=@();$subs=@();$squadUrl=''
    if($cache.matches.Contains($f.date)){$m=$cache.matches[$f.date];$starters=@($m.starters);$subs=@($m.subs);$squadUrl=[string]$m.url}
    $fwpUrl=Find-FwpMatchUrl $fwpLinks $f.venue $f.opponent
    if($knownFwpMatchUrls.ContainsKey($f.date)){$fwpUrl=[string]$knownFwpMatchUrls[$f.date]}
    $fwp=$null
    if($fwpUrl){$fwp=Get-FwpMatchData $fwpUrl}
    if($starters.Count -lt 11 -and $null -ne $fwp -and @($fwp.players).Count -ge 11){$starters=@($fwp.players | Select-Object -First 11 | ForEach-Object {$_.name});$subs=@($fwp.players | Select-Object -Skip 11 | ForEach-Object {$_.name})}
    $scorerKeys=Get-ScorerKeys $f.goalscorers
    # Read the official report before building detail rows so unused named substitutes can be added to the bench.
    $official=Get-TivertonReportData $f.date $f.opponent $starters $subs $scorerKeys
    if($null -ne $official -and $official.reportSubs){
        $subList=New-Object System.Collections.Generic.List[string]
        foreach($n in @($subs)){if($n){$subList.Add([string]$n)}}
        foreach($n in @($official.reportSubs)){
            $nk=Name-Key ([string]$n)
            if(-not $nk){continue}
            $alreadyStarter=@($starters | Where-Object {(Name-Key $_) -eq $nk}).Count -gt 0
            $alreadySub=@($subList | Where-Object {(Name-Key $_) -eq $nk}).Count -gt 0
            if(-not $alreadyStarter -and -not $alreadySub){$subList.Add([string]$n)}
        }
        $subs=@($subList.ToArray())
    }
    # Verified matchday benches from the two latest official reports. These include unused substitutes,
    # which Tivvy Archive's 'Substitutes used' section does not list.
    $verifiedBench=@{
        '2026-09-29'=@('Billy Tucker','Aiden Horne','Asa Hall','Matt Wood','Caleb Pryce-Hall')
        '2026-10-03'=@('Asa Hall','Jack Kennell','Corey Koerner','Matt Wood')
    }
    if($verifiedBench.ContainsKey($f.date)){
        # For these verified reports, use the complete official bench in the report's own order.
        $subs=@($verifiedBench[$f.date])
    }
    $starterDetails=@(Build-PlayerDetails $starters $fwp $false $f.date $scorerKeys)
    $subDetails=@(Build-PlayerDetails $subs $fwp $true $f.date $scorerKeys)
    if($null -ne $official){
        Apply-OfficialReportData $starterDetails $official
        Apply-OfficialReportData $subDetails $official
        Write-Host ("    official report enrichment: {0}" -f $official.url) -ForegroundColor DarkGray
    }

    # Absolute verified goal fallback for the two newest league games. This is deliberately applied
    # after all other enrichment so Finn Roberts' penalty is never lost if a source parser changes.
    $verifiedFinalGoals=@{
        '2026-09-29'=@([pscustomobject]@{name='Owen Howe';minute='36'},[pscustomobject]@{name='Finn Roberts';minute='64'})
        '2026-10-03'=@([pscustomobject]@{name='Aiden Horne';minute='25'},[pscustomobject]@{name='Finn Roberts';minute='38'})
    }
    if($verifiedFinalGoals.ContainsKey($f.date)){
        foreach($vg in @($verifiedFinalGoals[$f.date])){
            $vk=Name-Key ([string]$vg.name); $vm=[string]$vg.minute
            foreach($pd in @($starterDetails)+@($subDetails)){
                if((Name-Key $pd.name) -eq $vk){$pd.goalCount=1;$pd.goalMinutes=@($vm)}
            }
        }
    }
    # Verified team-sheet facts from the official reports, applied last so source-site layout changes cannot remove them.
    $verifiedLatestFacts=@{
        '2026-09-29'=[pscustomobject]@{captain='Ed Palmer';off=@{'Ryan Keates'='57';'Josh Bissett'='85'};on=@{'Billy Tucker'='57';'Aiden Horne'='85'}}
        '2026-10-03'=[pscustomobject]@{captain='Ed Palmer';off=@{'Ryan Keates'='54';'Finn Roberts'='68';'Aaron Wellington'='71'};on=@{'Asa Hall'='54';'Corey Koerner'='68';'Jack Kennell'='71'}}
    }
    if($verifiedLatestFacts.ContainsKey($f.date)){
        $vf=$verifiedLatestFacts[$f.date]
        foreach($pd in @($starterDetails)+@($subDetails)){
            $pk=Name-Key $pd.name
            if($pk -eq (Name-Key ([string]$vf.captain))){$pd.captain=$true}
            foreach($nm in $vf.off.Keys){if($pk -eq (Name-Key ([string]$nm))){$pd.offMinute=[string]$vf.off[$nm]}}
            foreach($nm in $vf.on.Keys){if($pk -eq (Name-Key ([string]$nm))){$pd.onMinute=[string]$vf.on[$nm];$pd.used=$true}}
        }
    }
        # Known verified captain fallback for the opening league match if other sources are unavailable.
    if($f.date -eq '2026-08-08' -and -not @($starterDetails | Where-Object {$_.captain}).Count){
        foreach($pd in $starterDetails){ if((Name-Key $pd.name) -eq (Name-Key 'Ed Palmer')){$pd.captain=$true} }
    }
    $captain=@($starterDetails | Where-Object {$_.captain} | Select-Object -First 1)
    $usedSubs=@($subDetails | Where-Object {$_.onMinute}).Count
    Write-Host ("  {0} {1,-24} {2} starters + {3} subs; captain: {4}; used subs: {5}" -f $f.date,$f.opponent,$starters.Count,$subs.Count,$(if($captain.Count){$captain[0].name}else{'not found'}),$usedSubs) -ForegroundColor $(if($starters.Count -eq 11){'Green'}else{'Yellow'})
    $players=@($starters)+@($subs)
    $final.Add([pscustomobject]@{date=$f.date;venue=$f.venue;opponent=$f.opponent;result=$f.result;goalscorers=$f.goalscorers;starters=$starters;subs=$subs;starterDetails=$starterDetails;subDetails=$subDetails;players=$players;squadUrl=$squadUrl;fwpUrl=$fwpUrl;officialReportUrl=$(if($null -ne $official){$official.url}else{''})})
}
$out=[ordered]@{season='2026/27';club='Tiverton Town';comp='SL1';fixtures=@($final.ToArray());updated=(Get-Date).ToString('yyyy-MM-dd HH:mm:ss');source=$sourceUrl;lineupSource='Tivvy Archive squad.php pages';eventSource='TivertonTownFC.uk official match reports plus Football Web Pages'}
$json=$out | ConvertTo-Json -Depth 10 -Compress
$json | Set-Content $dataFile -Encoding UTF8
"window.TIVVY_DATA = $json;" | Set-Content $dataJsFile -Encoding UTF8


Write-Host ''
Write-Host 'SUCCESS: cloud fixture data updated.' -ForegroundColor Green
Write-Host 'Captain, goal times, used substitutions and unused named substitutes are enriched from Tiverton Town match reports and Football Web Pages.' -ForegroundColor Green

# Arithmetic regression checks for the fixed-source version audit.
# Run: pwsh -File analysis/verify_version_audit.ps1
# These checks are not a complete AddrLib or RTL simulation.
$ErrorActionPreference = 'Stop'
$script:checkCount = 0
function Check-Equal($actual, $expected, [string]$label) {
    if ("$actual" -ne "$expected") { throw "$label : got $actual; expected $expected" }
    $script:checkCount++
}
function TailCapacity([int]$blockLog, [bool]$thick) {
    $effective = $blockLog
    if ($thick) { $effective -= [int][math]::Floor(($blockLog - 8) / 3) }
    if ($effective -le 8) { return 1 }
    if ($effective -le 11) { return 1 + (1 -shl ($effective - 9)) }
    return $effective - 4
}
function TailOffset([int]$capacity,[int]$relative) {
    $reverse = [math]::Max(0, $capacity - 1 - $relative)
    if ($reverse -gt 6) { return 16 -shl $reverse }
    return $reverse -shl 8
}
function OriginMicro([int]$offset) {
    $mx=0; $my=0
    for($j=0; $j -lt 6; $j++) {
        $mx = $mx -bor ((($offset -shr (9+2*$j)) -band 1) -shl $j)
        $my = $my -bor ((($offset -shr (8+2*$j)) -band 1) -shl $j)
    }
    return @($mx,$my)
}
function PatternOffset([string[]]$pattern,[int]$x,[int]$y,[int]$sample) {
    $value=0
    for($i=0;$i -lt $pattern.Count;$i++){
        $term=$pattern[$i]
        if($term -eq '0'){continue}
        $coordinate=switch($term.Substring(0,1)){'X'{$x};'Y'{$y};'S'{$sample}}
        $bit=[int]$term.Substring(1)
        $value=$value -bor ((($coordinate -shr $bit) -band 1) -shl $i)
    }
    return $value
}
# Exhaust all fixed 2D block sizes, BPE and sample exponents in the excerpt's domain.
$cases2d=0
foreach($blockLog in @(8,12,16,18)){
    foreach($elemLog in 0..4){
        foreach($sampleLog in 0..3){
            $n=$blockLog-$elemLog-$sampleLog
            $rtlWidth=[int][math]::Floor($n/2)+(($n -band 1) -band (($elemLog -band 1) -bor ($sampleLog -band 1)))
            $rtlHeight=[int][math]::Floor($n/2)
            $upWidth=($blockLog -shr 1)-($elemLog -shr 1)-($sampleLog -shr 1)-($elemLog -band $sampleLog -band 1)
            $upHeight=($blockLog -shr 1)-($elemLog -shr 1)-($sampleLog -shr 1)-(($elemLog -bor $sampleLog) -band 1)
            Check-Equal $rtlWidth $upWidth "2D width L=$blockLog e=$elemLog s=$sampleLog"
            Check-Equal $rtlHeight $upHeight "2D height"
            Check-Equal ($rtlWidth+$rtlHeight+$elemLog+$sampleLog) $blockLog '2D byte volume'
            $cases2d++
        }
    }
}
# All 15 excerpt 3D log2-dimension rows.
$expected3d=@{
    12=@('4,4,4','3,4,4','3,4,3','3,3,3','2,3,3')
    16=@('6,5,5','5,5,5','5,5,4','5,4,4','4,4,4')
    18=@('6,6,6','5,6,6','5,6,5','5,5,5','4,5,5')
}
foreach($blockLog in @(12,16,18)){
    foreach($elemLog in 0..4){
        $common=[int][math]::Floor($blockLog/3)-[int][math]::Floor($elemLog/3)
        $wx=$common+[int](($blockLog%3) -gt 0)-[int](($elemLog%3) -gt 0)
        $hy=$common
        $dz=$common+[int](($blockLog%3) -gt 1)-[int](($elemLog%3) -gt 1)
        Check-Equal "$wx,$hy,$dz" $expected3d[$blockLog][$elemLog] '3D dimensions'
        Check-Equal ($wx+$hy+$dz+$elemLog) $blockLog '3D byte volume'
    }
}
Check-Equal (TailCapacity 12 $false) 8 '4KB 2D capacity'
Check-Equal (TailCapacity 16 $false) 12 '64KB 2D capacity'
Check-Equal (TailCapacity 18 $false) 14 '256KB 2D capacity'
Check-Equal (TailCapacity 12 $true) 5 '4KB 3D capacity'
Check-Equal (TailCapacity 16 $true) 10 '64KB 3D capacity'
Check-Equal (TailCapacity 18 $true) 11 '256KB 3D capacity'
Check-Equal (TailOffset 12 5) 1536 'reverse6 boundary'
Check-Equal (TailOffset 12 4) 2048 'reverse7 boundary'
Check-Equal (TailOffset 12 17) 0 'non-tail sentinel'
Check-Equal (12-6) 6 'last reverse when capacity12 actual6'
Check-Equal ((1 -shl (16-8))*256) 65536 '256B offset units'
Check-Equal ((OriginMicro 0x1000) -join ',') '0,4' '0x1000 bit extraction'
Check-Equal ((OriginMicro 0x2000) -join ',') '4,0' '0x2000 bit extraction'
# Patterns copied from fixed gfx12SwizzlePattern.h indices, low address bit first.
$pattern1='X0,X1,Y0,X2,Y1,Y2,X3,Y3'.Split(',')
Check-Equal (PatternOffset $pattern1 4 2 0) 0x18 'Example1 block offset'
Check-Equal (0x10000000+5*256+(PatternOffset $pattern1 4 2 0)) 0x10000518 'Example1 final'
$pattern2='0,0,S0,S1,X0,Y0,X1,Y1,Y2,X2,Y3,X3,Y4,X4,Y5,X5'.Split(',')
Check-Equal (PatternOffset $pattern2 2 6 2) 0x1c8 'Example2 upstream pattern'
Check-Equal (0x20000000+18*65536+(PatternOffset $pattern2 2 6 2)) 0x201201c8 'Example2 final XOR0'
$oldPattern2='0,0,S0,S1,X0,Y0,X1,Y1,X2,Y2,Y3,X3,Y4,X4,Y5,X5'.Split(',')
Check-Equal (PatternOffset $oldPattern2 2 6 2) 0x2c8 'Old text actual arithmetic'
$first=13
for($level=0;$level -le 12;$level++){
    $dim=[int][math]::Ceiling(256/[math]::Pow(2,$level))
    if(($dim -le 64) -and ($dim -le 32) -and ((13-$level) -le 11)){$first=$level;break}
}
Check-Equal $first 3 'Example3 first mip, size AND count'
Check-Equal (TailOffset 11 (4-$first)) 0x2000 'Example3 offset'
$micro=OriginMicro (TailOffset 11 (4-$first))
Check-Equal "$($micro[0]*8),$($micro[1]*4),0" '32,0,0' 'Example3 origin'
Check-Equal ((0x05523400+0x40000-1) -band (-bnot (0x40000-1))) 0x05540000 'Old alignment arithmetic'
# Verify nested ceil on a non-power-of-two width over multiple blocks/mips.
foreach($dim in @(1,7,13,255,257,1025)){
    foreach($alignLog in @(2,4,6)){
        foreach($mip in 0..8){
            $lhs=[math]::Ceiling([math]::Ceiling($dim/[math]::Pow(2,$alignLog))/[math]::Pow(2,$mip))
            $rhs=[math]::Ceiling($dim/[math]::Pow(2,$alignLog+$mip))
            Check-Equal $lhs $rhs 'nested ceil'
        }
    }
}
Write-Output "PASS: $script:checkCount checks; $cases2d 2D configurations; 15 3D rows; tail, units and examples."

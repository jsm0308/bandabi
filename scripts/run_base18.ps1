param(
  [string]$BaseCommon = "configs/base.yaml",
  [string]$Sweep = "configs/sweeps/base18_single.yaml",
  [string]$ExpTag = "base18"
)

$baselines = @(
  "configs/baselines/greedy.yaml",
  "configs/baselines/cluster_first.yaml",
  "configs/baselines/local_search.yaml"
)

$scenarios = @(
  "configs/scenarios/seoul_allgu_v1.yaml",
  "configs/scenarios/rush_hour.yaml",
  "configs/scenarios/demand_spike.yaml",
  "configs/scenarios/spatial_skew.yaml",
  "configs/scenarios/wheelchair_heavy.yaml",
  "configs/scenarios/tight_constraints.yaml"
)

foreach ($b in $baselines) {
  $bName = [System.IO.Path]::GetFileNameWithoutExtension($b)

  foreach ($s in $scenarios) {
    $sName = [System.IO.Path]::GetFileNameWithoutExtension($s)
    $tag = "${ExpTag}__${bName}__${sName}"

    Write-Host "RUN: baseline=$bName scenario=$sName exp_tag=$tag"

    python -m bandabi.cli `
      --base $BaseCommon `
      --base $b `
      --scenario $s `
      --sweep $Sweep `
      --exp-tag $tag
  }
}

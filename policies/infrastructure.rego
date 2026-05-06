package swiftdeploy.infrastructure

import rego.v1

violations contains msg if {
  input.disk_free_gb < input.thresholds.min_disk_free_gb
  msg := sprintf("Disk free %.2fGB is below required %.2fGB", [input.disk_free_gb, input.thresholds.min_disk_free_gb])
}

violations contains msg if {
  input.cpu_load > input.thresholds.max_cpu_load
  msg := sprintf("CPU load %.2f is above allowed %.2f", [input.cpu_load, input.thresholds.max_cpu_load])
}

allow if {
  count(violations) == 0
}

decision := {
  "allow": true,
  "domain": "infrastructure",
  "reasons": ["Infrastructure policy passed"]
} if {
  allow
}

decision := {
  "allow": false,
  "domain": "infrastructure",
  "reasons": violations
} if {
  not allow
}

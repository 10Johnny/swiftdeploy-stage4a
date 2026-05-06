package swiftdeploy.canary

import rego.v1

violations contains msg if {
  input.error_rate_percent > input.thresholds.max_error_rate_percent
  msg := sprintf("Error rate %.2f%% is above allowed %.2f%%", [input.error_rate_percent, input.thresholds.max_error_rate_percent])
}

violations contains msg if {
  input.p99_latency_ms > input.thresholds.max_p99_latency_ms
  msg := sprintf("P99 latency %.2fms is above allowed %.2fms", [input.p99_latency_ms, input.thresholds.max_p99_latency_ms])
}

allow if {
  count(violations) == 0
}

decision := {
  "allow": true,
  "domain": "canary",
  "reasons": ["Canary safety policy passed"]
} if {
  allow
}

decision := {
  "allow": false,
  "domain": "canary",
  "reasons": violations
} if {
  not allow
}

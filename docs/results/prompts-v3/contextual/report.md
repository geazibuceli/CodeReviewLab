# Evaluation

Controlled synthetic benchmark; not real-repository performance.

Dataset SHA256: f4007402ebb2aaa5c552d1996c44f18b7e3446eaf5e4e67d4e9a94a7f8f00494

| Metric | Value |
| --- | --- |
| examples | 84 |
| processed | 78 |
| failures | 6 |
| coverage | 0.9285714285714286 |
| true_positives | 3 |
| false_positives | 47 |
| expected_bugs | 42 |
| finding_precision | 0.06 |
| bug_recall | 0.07142857142857142 |
| correct_function_false_positive_rate | 0.7105263157894737 |
| localization_accuracy | 0.5 |
| valid_output_rate | 0.9285714285714286 |
| mean_latency_seconds | 1.2894285178578382 |
| peak_gpu_memory_bytes | 3150485504 |

| Example | Status | TP | FP |
| --- | --- | --- | --- |
| boundary_condition-00-0-bug | parse_error | 0 | 0 |
| boundary_condition-00-0-correct | ok | 0 | 1 |
| boundary_condition-00-1-bug | ok | 0 | 0 |
| boundary_condition-00-1-correct | ok | 0 | 0 |
| boundary_condition-01-0-bug | ok | 0 | 0 |
| boundary_condition-01-0-correct | parse_error | 0 | 0 |
| boundary_condition-01-1-bug | ok | 0 | 0 |
| boundary_condition-01-1-correct | ok | 0 | 0 |
| boundary_condition-04-0-bug | ok | 1 | 0 |
| boundary_condition-04-0-correct | ok | 0 | 0 |
| boundary_condition-04-1-bug | ok | 0 | 0 |
| boundary_condition-04-1-correct | ok | 0 | 0 |
| boundary_condition-05-0-bug | ok | 1 | 0 |
| boundary_condition-05-0-correct | ok | 0 | 1 |
| boundary_condition-05-1-bug | ok | 1 | 0 |
| boundary_condition-05-1-correct | ok | 0 | 1 |
| boundary_condition-06-0-bug | ok | 0 | 0 |
| boundary_condition-06-0-correct | ok | 0 | 1 |
| boundary_condition-06-1-bug | ok | 0 | 1 |
| boundary_condition-06-1-correct | ok | 0 | 0 |
| boundary_condition-08-0-bug | ok | 0 | 0 |
| boundary_condition-08-0-correct | ok | 0 | 0 |
| boundary_condition-08-1-bug | ok | 0 | 1 |
| boundary_condition-08-1-correct | ok | 0 | 0 |
| boundary_condition-09-0-bug | ok | 0 | 0 |
| boundary_condition-09-0-correct | ok | 0 | 0 |
| boundary_condition-09-1-bug | ok | 0 | 0 |
| boundary_condition-09-1-correct | ok | 0 | 0 |
| none_or_empty-00-0-bug | ok | 0 | 1 |
| none_or_empty-00-0-correct | ok | 0 | 1 |
| none_or_empty-00-1-bug | ok | 0 | 0 |
| none_or_empty-00-1-correct | ok | 0 | 1 |
| none_or_empty-01-0-bug | ok | 0 | 1 |
| none_or_empty-01-0-correct | ok | 0 | 1 |
| none_or_empty-01-1-bug | ok | 0 | 1 |
| none_or_empty-01-1-correct | ok | 0 | 1 |
| none_or_empty-04-0-bug | ok | 0 | 1 |
| none_or_empty-04-0-correct | ok | 0 | 1 |
| none_or_empty-04-1-bug | ok | 0 | 1 |
| none_or_empty-04-1-correct | ok | 0 | 1 |
| none_or_empty-05-0-bug | ok | 0 | 1 |
| none_or_empty-05-0-correct | ok | 0 | 1 |
| none_or_empty-05-1-bug | ok | 0 | 1 |
| none_or_empty-05-1-correct | parse_error | 0 | 0 |
| none_or_empty-06-0-bug | ok | 0 | 1 |
| none_or_empty-06-0-correct | ok | 0 | 1 |
| none_or_empty-06-1-bug | ok | 0 | 1 |
| none_or_empty-06-1-correct | ok | 0 | 1 |
| none_or_empty-08-0-bug | ok | 0 | 1 |
| none_or_empty-08-0-correct | parse_error | 0 | 0 |
| none_or_empty-08-1-bug | parse_error | 0 | 0 |
| none_or_empty-08-1-correct | parse_error | 0 | 0 |
| none_or_empty-09-0-bug | ok | 0 | 1 |
| none_or_empty-09-0-correct | ok | 0 | 1 |
| none_or_empty-09-1-bug | ok | 0 | 1 |
| none_or_empty-09-1-correct | ok | 0 | 1 |
| mutable_default-00-0-bug | ok | 0 | 1 |
| mutable_default-00-0-correct | ok | 0 | 1 |
| mutable_default-00-1-bug | ok | 0 | 0 |
| mutable_default-00-1-correct | ok | 0 | 1 |
| mutable_default-01-0-bug | ok | 0 | 0 |
| mutable_default-01-0-correct | ok | 0 | 1 |
| mutable_default-01-1-bug | ok | 0 | 0 |
| mutable_default-01-1-correct | ok | 0 | 0 |
| mutable_default-04-0-bug | ok | 0 | 0 |
| mutable_default-04-0-correct | ok | 0 | 1 |
| mutable_default-04-1-bug | ok | 0 | 0 |
| mutable_default-04-1-correct | ok | 0 | 1 |
| mutable_default-05-0-bug | ok | 0 | 1 |
| mutable_default-05-0-correct | ok | 0 | 1 |
| mutable_default-05-1-bug | ok | 0 | 0 |
| mutable_default-05-1-correct | ok | 0 | 1 |
| mutable_default-06-0-bug | ok | 0 | 1 |
| mutable_default-06-0-correct | ok | 0 | 1 |
| mutable_default-06-1-bug | ok | 0 | 1 |
| mutable_default-06-1-correct | ok | 0 | 1 |
| mutable_default-08-0-bug | ok | 0 | 1 |
| mutable_default-08-0-correct | ok | 0 | 1 |
| mutable_default-08-1-bug | ok | 0 | 1 |
| mutable_default-08-1-correct | ok | 0 | 1 |
| mutable_default-09-0-bug | ok | 0 | 0 |
| mutable_default-09-0-correct | ok | 0 | 1 |
| mutable_default-09-1-bug | ok | 0 | 0 |
| mutable_default-09-1-correct | ok | 0 | 0 |

# Evaluation

Controlled synthetic benchmark; not real-repository performance.

Dataset SHA256: f4007402ebb2aaa5c552d1996c44f18b7e3446eaf5e4e67d4e9a94a7f8f00494

| Metric | Value |
| --- | --- |
| examples | 84 |
| processed | 80 |
| failures | 4 |
| coverage | 0.9523809523809523 |
| true_positives | 2 |
| false_positives | 67 |
| expected_bugs | 42 |
| finding_precision | 0.028985507246376812 |
| bug_recall | 0.047619047619047616 |
| correct_function_false_positive_rate | 0.85 |
| localization_accuracy | 0.2 |
| valid_output_rate | 0.9523809523809523 |
| mean_latency_seconds | 1.8698995202382018 |
| peak_gpu_memory_bytes | 3149914112 |

| Example | Status | TP | FP |
| --- | --- | --- | --- |
| boundary_condition-00-0-bug | ok | 1 | 0 |
| boundary_condition-00-0-correct | ok | 0 | 1 |
| boundary_condition-00-1-bug | ok | 0 | 1 |
| boundary_condition-00-1-correct | ok | 0 | 0 |
| boundary_condition-01-0-bug | ok | 1 | 0 |
| boundary_condition-01-0-correct | ok | 0 | 1 |
| boundary_condition-01-1-bug | ok | 0 | 0 |
| boundary_condition-01-1-correct | ok | 0 | 1 |
| boundary_condition-04-0-bug | ok | 0 | 1 |
| boundary_condition-04-0-correct | parse_error | 0 | 0 |
| boundary_condition-04-1-bug | ok | 0 | 0 |
| boundary_condition-04-1-correct | ok | 0 | 0 |
| boundary_condition-05-0-bug | ok | 0 | 1 |
| boundary_condition-05-0-correct | ok | 0 | 1 |
| boundary_condition-05-1-bug | parse_error | 0 | 0 |
| boundary_condition-05-1-correct | ok | 0 | 1 |
| boundary_condition-06-0-bug | ok | 0 | 1 |
| boundary_condition-06-0-correct | ok | 0 | 1 |
| boundary_condition-06-1-bug | ok | 0 | 1 |
| boundary_condition-06-1-correct | ok | 0 | 0 |
| boundary_condition-08-0-bug | ok | 0 | 1 |
| boundary_condition-08-0-correct | ok | 0 | 0 |
| boundary_condition-08-1-bug | ok | 0 | 1 |
| boundary_condition-08-1-correct | ok | 0 | 1 |
| boundary_condition-09-0-bug | ok | 0 | 0 |
| boundary_condition-09-0-correct | ok | 0 | 0 |
| boundary_condition-09-1-bug | ok | 0 | 0 |
| boundary_condition-09-1-correct | ok | 0 | 0 |
| none_or_empty-00-0-bug | ok | 0 | 1 |
| none_or_empty-00-0-correct | ok | 0 | 1 |
| none_or_empty-00-1-bug | ok | 0 | 1 |
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
| none_or_empty-08-0-correct | ok | 0 | 1 |
| none_or_empty-08-1-bug | parse_error | 0 | 0 |
| none_or_empty-08-1-correct | ok | 0 | 1 |
| none_or_empty-09-0-bug | ok | 0 | 1 |
| none_or_empty-09-0-correct | ok | 0 | 1 |
| none_or_empty-09-1-bug | ok | 0 | 1 |
| none_or_empty-09-1-correct | ok | 0 | 1 |
| mutable_default-00-0-bug | ok | 0 | 1 |
| mutable_default-00-0-correct | ok | 0 | 1 |
| mutable_default-00-1-bug | ok | 0 | 1 |
| mutable_default-00-1-correct | ok | 0 | 1 |
| mutable_default-01-0-bug | ok | 0 | 0 |
| mutable_default-01-0-correct | ok | 0 | 1 |
| mutable_default-01-1-bug | ok | 0 | 1 |
| mutable_default-01-1-correct | ok | 0 | 1 |
| mutable_default-04-0-bug | ok | 0 | 1 |
| mutable_default-04-0-correct | ok | 0 | 1 |
| mutable_default-04-1-bug | ok | 0 | 1 |
| mutable_default-04-1-correct | ok | 0 | 1 |
| mutable_default-05-0-bug | ok | 0 | 1 |
| mutable_default-05-0-correct | ok | 0 | 1 |
| mutable_default-05-1-bug | ok | 0 | 1 |
| mutable_default-05-1-correct | ok | 0 | 1 |
| mutable_default-06-0-bug | ok | 0 | 1 |
| mutable_default-06-0-correct | ok | 0 | 1 |
| mutable_default-06-1-bug | ok | 0 | 1 |
| mutable_default-06-1-correct | ok | 0 | 1 |
| mutable_default-08-0-bug | ok | 0 | 1 |
| mutable_default-08-0-correct | ok | 0 | 1 |
| mutable_default-08-1-bug | ok | 0 | 1 |
| mutable_default-08-1-correct | ok | 0 | 1 |
| mutable_default-09-0-bug | ok | 0 | 1 |
| mutable_default-09-0-correct | ok | 0 | 1 |
| mutable_default-09-1-bug | ok | 0 | 1 |
| mutable_default-09-1-correct | ok | 0 | 1 |

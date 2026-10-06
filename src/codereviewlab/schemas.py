"""Strict shared contracts for extraction, reviewers, datasets, and evaluation."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Category(StrEnum):
    BOUNDARY = "boundary_condition"
    NONE_EMPTY = "none_or_empty"
    MUTABLE = "mutable_default"


class FunctionInput(StrictModel):
    path: str
    name: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    code: str = Field(min_length=1)
    context: str = ""

    @model_validator(mode="after")
    def check_lines(self):
        if self.end_line < self.start_line:
            raise ValueError("end_line precedes start_line")
        if len(self.code.splitlines()) != self.end_line - self.start_line + 1:
            raise ValueError("code and source line range disagree")
        return self


class Finding(StrictModel):
    path: str
    line: int = Field(ge=1)
    category: Category
    explanation: str = Field(min_length=1)
    suggested_fix: str = Field(min_length=1)


class StructuredResponse(StrictModel):
    findings: list[Finding]


class InferenceMetadata(StrictModel):
    backend: str
    model: str | None = None
    revision: str | None = None
    prompt_version: str | None = None
    generation: dict = Field(default_factory=dict)
    device: str = "cpu"
    latency_seconds: float = Field(default=0, ge=0)
    peak_gpu_memory_bytes: int | None = None
    adapter: str | None = None
    adapter_hash: str | None = None


class ReviewResult(StrictModel):
    function: FunctionInput
    status: Literal["ok", "inference_error", "parse_error", "input_error"]
    findings: list[Finding] = Field(default_factory=list)
    error: str | None = None
    raw_response: str | None = None
    metadata: InferenceMetadata

    @model_validator(mode="after")
    def check_result(self):
        if self.status != "ok" and (self.findings or not self.error):
            raise ValueError("failure requires error and no findings")
        for finding in self.findings:
            if finding.path != self.function.path or not (
                self.function.start_line <= finding.line <= self.function.end_line
            ):
                raise ValueError("finding is outside the reviewed function")
        return self


class ExpectedFinding(StrictModel):
    category: Category
    accepted_lines: list[int] = Field(min_length=1)
    explanation: str = Field(min_length=1)
    suggested_fix: str = Field(min_length=1)


class ReferenceCase(StrictModel):
    calls: list[dict] = Field(min_length=1)
    expected: list


class Example(StrictModel):
    id: str
    family_id: str
    provenance: str
    review_status: Literal["author_reviewed", "pending"]
    split: Literal["dev", "test", "train", "fixture"]
    function: FunctionInput
    buggy: bool
    expected_findings: list[ExpectedFinding]
    reference_cases: list[ReferenceCase] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_labels(self):
        if self.buggy != bool(self.expected_findings):
            raise ValueError("bug label must agree with expected findings")
        for finding in self.expected_findings:
            if not all(
                self.function.start_line <= n <= self.function.end_line
                for n in finding.accepted_lines
            ):
                raise ValueError("accepted finding location outside function")
        return self


class EvaluationMetrics(StrictModel):
    examples: int
    processed: int
    failures: int
    coverage: float | None
    true_positives: int
    false_positives: int
    expected_bugs: int
    finding_precision: float | None
    bug_recall: float | None
    correct_function_false_positive_rate: float | None
    localization_accuracy: float | None
    valid_output_rate: float | None
    mean_latency_seconds: float | None
    peak_gpu_memory_bytes: int | None

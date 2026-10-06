# Development prompt selection protocol

Recorded before inspecting the completed development experiment results.

Compare basic, few-shot, and contextual prompts using the same pinned model, greedy decoding,
seed 42, input budget 4,096, output budget 512, and prompt version review-v3. All runs use the
same development file. Reserved test results are not used in this choice.

Choose the highest finding F1, defined as `2 * precision * recall / (precision + recall)`;
undefined precision or a zero denominator gives a selection score of zero. Failure examples
remain in the recall denominator. Break ties by higher valid-output rate, then prefer basic,
few-shot, and contextual in that order. This small synthetic benchmark is insufficient for
generalized prompt recommendations. Preserve failures and full raw responses for inspection.

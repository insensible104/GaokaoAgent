export type CareerAssessmentMode = "skip" | "quick" | "complete";

export interface CareerAssessmentPayload {
  mode: CareerAssessmentMode;
  answers: Record<string, number>;
  mbti_type?: string;
  career_values: string[];
}

const RIASEC_CODES = ["R", "I", "A", "S", "E", "C"];

export const requiredCareerQuestionIds = (mode: CareerAssessmentMode) => {
  if (mode === "skip") return [];
  const maxIndex = mode === "quick" ? 2 : 5;
  return RIASEC_CODES.flatMap((code) =>
    Array.from({ length: maxIndex }, (_, index) => `${code}${index + 1}`),
  );
};

export const isCareerAssessmentComplete = (value: CareerAssessmentPayload) => {
  const requiredIds = requiredCareerQuestionIds(value.mode);
  return requiredIds.every((id) => Number.isInteger(value.answers[id]) && value.answers[id] >= 1 && value.answers[id] <= 5);
};

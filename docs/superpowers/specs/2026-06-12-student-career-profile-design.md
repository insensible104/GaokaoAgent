# Student Career Profile Design

## Problem Anchor

PathFinder needs a richer student record within the one-week Guangdong New Gaokao MVP window, but profile richness must improve recommendation fidelity rather than add decorative labels.

## Product Boundary

- Students choose `skip`, `quick` (12 questions), or `complete` (30 questions).
- RIASEC/Holland is the measured career-interest signal. The backend owns scoring and provenance.
- MBTI is optional self-reported context. It is displayed as a communication/self-reflection label and never changes admission probability or hard-filters majors.
- Career values are explicit student statements and are recorded for explanation; this release does not use them in admission probability.
- Explicit major preferences and blacklists remain stronger than interest-profile affinity.

## Data Contract

`delivery_profile.career_assessment` carries:

- `mode`: `skip | quick | complete`
- `answers`: question-id to integer score in `[1, 5]`
- `mbti_type`: optional 16-type code
- `career_values`: up to three known value codes

The backend derives:

- normalized `holland_code` dimensions
- `riasec_top_codes`
- `career_assessment_status`
- provenance entries marked `measured_assessment` or `user_explicit`

## Recommendation Use

Major taxonomy categories receive a small RIASEC affinity signal. The signal may add at most `0.15` to major utility and produces an explanation reason. It cannot rescue a blacklisted major, alter admission probability, or override an explicit major mismatch penalty.

## User Experience

The existing form gains a separate student-profile section. Quick and complete modes use the same five-point response control and require all visible questions. Results show the measured RIASEC top code, optional MBTI, and career values in the explicit-profile evidence band.

## Verification

- Known answer patterns produce deterministic RIASEC scores and top codes.
- Incomplete or invalid assessments are rejected.
- MBTI does not change major utility when all other fields are equal.
- RIASEC changes utility for aligned versus misaligned majors.
- Blacklists remain absolute.
- Browser verification covers quick/complete selection and mobile layout.

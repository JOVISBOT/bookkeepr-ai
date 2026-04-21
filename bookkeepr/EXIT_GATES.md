# Exit Gate Criteria - BookKeepr Growth Cycle

## Gate Structure
Every phase ends with a GATE. No exceptions. Gate has:
- **Criteria**: Measurable pass/fail conditions
- **Status**: `pending` | `running` | `passed` | `failed` | `blocked`
- **Measurer**: Agent that runs the test
- **Validator**: Agent that reviews results
- **Escalation**: After 5 failures, escalate to human

---

## Phase 3: TEST Gates

### Gate 3.1: Unit Tests & Build
**Purpose:** Code compiles and passes static analysis

| # | Criteria | Method | Pass Threshold |
|---|----------|--------|----------------|
| 1 | TypeScript compilation | `tsc -b` | 0 errors |
| 2 | Vite build | `npm run build` | Exit code 0 |
| 3 | Bundle size check | `du -k dist/assets/*.js` | < 500KB initial |
| 4 | PRS scan | `grep -rn "TODO\|FIXME" src/` | 0 matches |
| 5 | No test failures | `npm test` (if exists) | 0 failures |

**Measurer:** Builder
**Validator:** Bossman (review PR, run PRS)
**On Fail:** Builder fixes → Re-measure (max 5 iterations)

---

### Gate 3.2: Integration Tests
**Purpose:** Components work together in browser

| # | Criteria | Method | Pass Threshold |
|---|----------|--------|----------------|
| 1 | Dev server starts | `npm run dev` | No crash |
| 2 | Dashboard loads | Navigate to `/` | < 3s load time |
| 3 | Lazy routes work | Navigate to `/billing` | Chunk loads, no 404 |
| 4 | No console errors | Browser DevTools | 0 errors |
| 5 | Mobile responsive | Chrome DevTools mobile | Layout intact |

**Measurer:** Builder
**Validator:** Bossman (manual spot-check)
**On Fail:** Builder debug → Re-test

---

### Gate 3.3: Performance Validation
**Purpose:** Metrics hit improvement targets

| # | Criteria | Method | Pass Threshold |
|---|----------|--------|----------------|
| 1 | Bundle measured | Build output | Baseline + target met |
| 2 | DB concurrency | Load test script | 10+ concurrent reads |
| 3 | API call reduction | Network tab / logs | 60% fewer calls |
| 4 | Lighthouse score | `lighthouse` CLI | > 90 performance |

**Measurer:** Builder
**Validator:** Bossman (compare to baseline)
**On Fail:** Revert or re-architect

---

## Phase 4: DELIVER Gates

### Gate 4.1: Final Review
**Purpose:** Production-ready polish

| # | Criteria | Method | Pass Threshold |
|---|----------|--------|----------------|
| 1 | PRS clear | Pre-commit hook | Pass |
| 2 | Documentation | README updated | Instructions complete |
| 3 | Rollback plan | Documented in commit | Can revert in < 5 min |
| 4 | Metrics captured | state/project.json | Before/after logged |

---

### Gate 4.2: Deployment
**Purpose:** Live in production

| # | Criteria | Method | Pass Threshold |
|---|----------|--------|----------------|
| 1 | Vercel build | `vercel --prod` | Success |
| 2 | Smoke test | curl production URL | 200 OK |
| 3 | Feature works | Manual test | Acceptance criteria met |

---

### Gate 4.3: Verification
**Purpose:** Confirmed working in wild

| # | Criteria | Method | Pass Threshold |
|---|----------|--------|----------------|
| 1 | No error spikes | Vercel logs | < 5% 5xx errors |
| 2 | Performance stable | Lighthouse CI | Score maintained |
| 3 | User acceptance | Spot check | No critical bugs |

---

## Phase 5: ARCHIVE Gates

### Gate 5.1: Capture
All outputs saved to state/

### Gate 5.2: Catalog
Files organized, commit tagged

### Gate 5.3: Close
Final report generated, lessons captured

---

## Gate Decision Protocol

```
BUILDER: [MEASUREMENT RESULTS]
  ↓
BOSSMAN: Review → ALL criteria met?
  ↓ YES → "GATE [X.Y] PASSED" → Next phase
  ↓ NO  → "GATE [X.Y] FAILED [N/5]" → Back to BUILDER
  ↓
After 5 failures → "ESCALATION: [reason]" → JOVIS decides
```

## Required Phrases

| Who | When | Phrase |
|-----|------|--------|
| Measurer | Complete | "GATE [X.Y] MEASUREMENT: [metric]=[value]" |
| Validator | Pass | "GATE [X.Y] PASSED - proceed to [next]" |
| Validator | Fail | "GATE [X.Y] FAILED [[N]/5]: [criteria] not met" |
| Validator | Block | "ESCALATION: [specific reason]" |

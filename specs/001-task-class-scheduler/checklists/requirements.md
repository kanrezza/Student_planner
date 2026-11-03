# Specification Quality Checklist: Quản lý công việc và lịch học cá nhân

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-04
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Validation passed on iteration 1.
- "Máy Mac" and "thông báo hệ thống" are platform constraints from the constitution
  (Principle IV), not implementation choices.
- Ambiguities resolved with documented defaults instead of clarification markers: bulk entry
  is a multi-row form (no file import); reminder defaults 15 min (class) / 1 h (task); tasks
  without a time are due at 23:59; reminders fire only while the app is running.
- 2026-11-04: Added User Story 6 "Nhập lịch học từ ảnh" (P2), FR-028–FR-036, SC-010–SC-013;
  reminders renumbered to User Story 7. Defaults chosen: one image per import, PNG/JPEG/HEIC
  up to 20 MB, duplicate = same subject or class code + date + start time.
- 2026-11-04: Aligned with constitution v2.0.0 (100% offline). Image recognition now runs
  entirely on-device: removed send-confirmation scenario, network/AI-failure scenario and
  FR, AI-service/API-key assumption; FR-029 now requires on-device recognition; FR-025 states
  the whole app is offline; SC-013 = no data or images leave the machine. FR-036 renumbered
  to FR-035. Re-validated: all items pass, no references to internet/AI services remain.
- 2026-11-04: Added User Story 8 (Ca học, P2), 9 (Nhãn, P2), 10 (Tự tạo deadline, P3) with
  FR-038–FR-050 and SC-014–SC-016. Reminders scoped to browser notifications while the app tab
  is open; iPhone reminders (former FR-038–FR-041, SC-014, never committed) removed and their
  IDs reused. "Trình duyệt" is a user-stated product constraint, not an implementation leak.
  Re-validated: all items pass.
- 2026-11-04: Restored sync to Apple Calendar/Reminders via the user's iCloud (constitution
  v2.2.0): FR-051–FR-054, SC-017–SC-018, User Story 7 scenarios 6–10, related edge cases and
  assumptions. Browser notifications kept only as a fallback when sync is off (FR-021).
  User Stories 8–10 unchanged. Re-validated: all items pass.
- 2026-11-04: Added User Story 11 "Lịch thi" (P2) with FR-055–FR-064, SC-019–SC-021, 6 edge cases,
  2 assumptions; FR-027 now includes exams. Exam reminders reuse the Calendar/Reminders sync
  (FR-064) with minimal fields (no candidate number / exam format). Student-info columns in exam
  screenshots are dropped and never stored (FR-061). Requirements describe the exam table
  generically ("cổng sinh viên"), without naming a specific school. Re-validated: all items pass.

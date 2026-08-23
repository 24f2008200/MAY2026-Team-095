# Smart Society Complaint Workflow Audit & Fixes

Date: 2026-08-18

## Enforced lifecycle

`OPEN / REOPENED -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED`

- A resident creates a complaint as `OPEN`.
- Only an admin can assign or reassign staff.
- Assignment moves the complaint to `ASSIGNED`.
- Only the currently assigned staff member can move `ASSIGNED -> IN_PROGRESS -> RESOLVED`.
- A resident can accept/close a resolved complaint, submit a review (which closes it), or reopen it within 7 days when no feedback has been submitted.
- Reopening removes the previous staff assignment and returns the complaint to `REOPENED` admin triage. It must be assigned again before staff can work on it.
- Resolved/closed complaint timelines and attachments are read-only until a valid reopen.

## Role and visibility rules

### Resident
- Can list/view only their own complaints.
- Can edit their own `OPEN` or `REOPENED` complaints.
- Can comment/upload only while their complaint is active.
- Can close their own active or resolved complaint.
- Can reopen their own `RESOLVED` or `CLOSED` complaint within 7 days if feedback has not been submitted.
- Can submit feedback only on a resolved/closed complaint.

### Staff
- Live queue contains only complaints assigned to that staff member and in `ASSIGNED`/`IN_PROGRESS`.
- Cannot view an unassigned complaint or another staff member's complaint by changing the URL.
- Can only transition `ASSIGNED -> IN_PROGRESS -> RESOLVED`.
- Cannot assign/reassign complaints.
- Cannot close or reopen complaints.
- Cannot comment/upload after the complaint is no longer active work assigned to them.

### Admin
- Can view all complaints.
- Is the only role allowed to assign/reassign staff.
- Can close active/resolved complaints.
- Can comment/upload on active complaints.
- Reopened complaints return to the admin queue with no staff assignment.

## Major fixes applied

1. **Reopen logic fixed**
   - Resident-only ownership check.
   - Supports `RESOLVED` and `CLOSED` within the 7-day window.
   - Rejects reopening after feedback is submitted.
   - Clears `assigned_staff_id`, `resolved_at`, and `closed_at`.
   - Alerts admins and the previous technician.

2. **Staff visibility fixed**
   - `/staff/complaints` now returns only the authenticated technician's `ASSIGNED`/`IN_PROGRESS` work.
   - Direct complaint access remains protected by assignment checks.
   - Reopening removes the previous technician's access.

3. **Close authorization fixed**
   - The old generic close endpoint could be called by any authenticated role.
   - It is now restricted to ADMIN/RESIDENT, with resident ownership enforced in the service.

4. **Frontend action visibility centralized**
   - Added shared permission helpers in `frontend/js/utils.js`.
   - Assign/Reassign only appears for admins in valid states.
   - Log Work only appears for the currently assigned staff member.
   - Close/Reopen/Comment/Upload buttons use the same workflow rules across pages.

5. **Staff status UI fixed**
   - Removed the misleading `ASSIGNED` option from the staff status page.
   - Staff see only the next valid transition: Begin Work or Complete Task.

6. **Assignment page fixed**
   - Dispatch remarks are now sent to the backend and stored in the timeline.
   - Current assignee is preselected for reassignment.
   - Staff with a trade matching the complaint category are listed first as recommended.
   - Invalid/completed complaint states cannot use the assignment page.

7. **Staff deactivation fixed**
   - Deactivating staff now removes their active assignments and returns those complaints to the unassigned admin queue.
   - Residents are notified that reassignment is pending.
   - A deactivated user's old JWT is rejected on the next protected API request.

8. **Resolved vs closed timestamps fixed**
   - Added `closed_at` instead of reusing `resolved_at` for two different meanings.
   - Resolution reporting now remains based on actual resolution time.
   - Reopen timing uses the appropriate resolution/closure timestamp.

9. **Staff trade model fixed**
   - Added a real `users.trade` field instead of abusing `building` as the technician trade.
   - Existing staff trades are migrated from the previous `building` value.
   - Staff trade options now come from active complaint categories in the admin UI.

10. **UI consistency fixes**
   - Resident dashboard includes `REOPENED` in filters.
   - Review/reopen checks use `feedback.rating` consistently.
   - Status/priority CSS now supports backend enum casing (`OPEN`, `IN_PROGRESS`, etc.).
   - User-facing ticket IDs prefer `complaint_code` instead of the internal database ID.
   - “Messages” navigation was renamed to “Notifications”; complaint discussion remains in the complaint timeline.
   - Staff account form password validation now matches backend minimum length (8).
   - Staff removal wording now correctly says Deactivate.

11. **Dead mock store retired**
   - `frontend/js/store.js` contained stale localStorage complaints and plaintext demo passwords but was not used by the live pages.
   - It is now a harmless legacy placeholder so API state is the single source of truth.

12. **Backend cleanup**
   - Removed duplicate CORS initialization.
   - `backend/app.py` no longer defaults to Flask debug mode.

## Database migrations added

- `backend/migrations/versions/a18c6d9e4f21_add_closed_at_to_complaints.py`
- `backend/migrations/versions/b42f8c31d7a0_add_staff_trade.py`

Before deploying, back up the database and run from the `backend` directory:

```bash
flask --app app.py db upgrade
```

Do not deploy the new Python model code without applying the migrations first.

## Validation performed

- Python source and migration files pass `compileall` syntax validation.
- All frontend JavaScript files and every inline Vue/JavaScript block pass `node --check`.
- Static workflow assertions confirm the role decorators, staff queue filter, reopen assignment clearing, staff transition restrictions, migration fields, and frontend permission helpers are present.

The sandbox used for this audit does not have the project's Flask/SQLAlchemy dependencies installed, so an end-to-end Flask test client run could not be executed here. Run the manual workflow below after installing `backend/requirements.txt` and applying migrations.

## Manual smoke test after deployment

1. Resident creates a complaint -> `OPEN` and no staff can see it.
2. Staff attempts to open the complaint ID directly -> `403`.
3. Admin assigns Staff A -> `ASSIGNED`; only Staff A sees it.
4. Staff B attempts the direct URL -> `403`.
5. Staff A starts work -> `IN_PROGRESS`.
6. Staff A resolves -> `RESOLVED`.
7. Resident sees Review & Close / Accept & Close / Reopen choices as appropriate.
8. Resident reopens without feedback -> `REOPENED`, `assigned_staff_id = null`.
9. Staff A can no longer access the reopened complaint.
10. Admin assigns it again -> `ASSIGNED` and the new technician can work it.
11. Deactivate a technician with active work -> work returns to `OPEN`/unassigned admin triage.
12. Try the deactivated technician's existing token -> protected endpoints return `401`.

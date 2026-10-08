# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

EXAMPLE OUTPUT (Step 2: Create and Run a Demo Script)
Today's Schedule for Saniya (Tuesday, October 06)
--------------------------------------------------
07:30 AM  Morning walk     Sparky  30 min  (priority 1)
08:15 AM  Feed breakfast   Garfield  10 min  (priority 1)
02:00 PM  Vet check-up     Sparky  45 min  (priority 2)
06:30 PM  Brush fur        Garfield  15 min  (priority 3)

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

* Command to run tests in terminal: python3 -m pytest
The 37 tests in tests/test_pawpal.py cover the scheduling logic in pawpal_systems.py, with a mix of normal cases and edge cases:

- Tasks and ownership: completing a task, adding tasks to a pet, and rejecting a task for a pet the owner doesn't have.

- Sorting: sort_by_time orders tasks chronologically, puts untimed tasks last, and breaks ties by priority. Fully tied tasks stay in their original order, and prioritize moves completed tasks to the bottom.

- Filtering: by pet name (case-insensitive), by completion status, and for pets that have no tasks or don't exist.

- Recurring tasks: daily and weekly tasks create the next occurrence from today's date, whether completed early, on time or late. Completing a task twice doesn't create duplicates, and one-off tasks don't repeat. An unknown frequency is rejected.

- Conflict detection: two tasks at the same time, partial overlaps, one task inside another and three-way overlaps are caught, for one pet or several. Back-to-back tasks, untimed tasks and completed tasks aren't flagged. A task that runs past midnight is handled.

- Warnings: conflict messages name the pets involved and suggest the next free slot. Bad time data, such as mixing timezone-aware and naive datetimes, produces a warning instead of a crash.

- Planning: the schedule fits the most urgent tasks into the owner's available time. It also covers a task that exactly fills the remaining time, tasks longer than the budget, zero available time and an empty task list.

- Next free slot: it skips past adjacent tasks, uses a gap only when the task fits, ignores the task being moved, and returns the requested time unchanged if it's after every task.

TERMINAL OUTPUT AFTER RUNNING ALL 37 TEST CASES: 
=====================================test session starts ===================================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/slmacbook/Desktop/ai110-module2-pawpal-starter
plugins: anyio-4.15.1
collected 37 items                                                                                                                                          

tests/test_pawpal.py .....................................                                                                                            [100%]

========================================= 37 passed in 0.05s ===============================

CONFIDENCE LEVEL: 4

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

IN PAWPAL_SYSTEMS.PY
1. Urgency ordering key: _priority_key --> Builds the sort key (completed, priority, deadline, duration): incomplete tasks first, then lowest priority number, earliest deadline, shortest duration. Every other sort below uses it.

2. Sort the task list in place by urgency:	Scheduler.prioritize (line 89) --> Sorts self.tasks with _priority_key. The app calls this when you click Generate schedule.

3. Sort by start time:	Scheduler.sort_by_time  --> Returns a new list ordered by start_time. Untimed tasks go last, and ties are broken with _priority_key. It doesn't change self.tasks.

4. Urgency order inside planning:	Scheduler._plan --> Sorts the incomplete tasks with _priority_key, then picks greedily. fit_to_time, conflicting_tasks and unscheduled all use this order.

5. Urgency order for leftovers: Scheduler.unscheduled  --> 	Returns the tasks the plan left out, sorted by _priority_key.

6. Start-time order for slot search: Scheduler.next_free_slot --> Sorts the busy tasks by start_time to sweep for the first gap that fits.

IN APP.PY

7. Generate schedule: Calls prioritize() and fit_to_time(), then shows the plan table and how many of the available minutes are used.

8. Skipped-for-overlap warnings: One warning per task from conflicting_tasks(), with a suggested slot from next_free_slot().

9. Not-enough-time warning:	Lists unscheduled() tasks that weren't skipped for a conflict.

10. Live conflict warnings	app.py:165-167	Shows conflict_warnings() under the task list, as soon as tasks overlap.

11. Complete task and queue the next one: Calls complete_task() and reports the next due date for recurring tasks.

12. Add timed or recurring tasks: The "Set a start time" checkbox and "Repeats" dropdown feed the scheduling logic.



## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->
Features:
PawPal+ is a Streamlit app (streamlit run app.py) for planning pet care. From top to bottom, the page lets you:

* Set up the owner: enter your name and how many minutes you have available today.
* Add pets: enter name, species, birthday, weight, gender and color. Added pets appear in a table with their computed age.
* Add tasks: choose a title, a pet, a duration, a priority (high, medium or low) and how often it repeats (once, daily or weekly). You can also set an optional start time.
* View and filter tasks: filter by pet and by status (All, To do, Done), and toggle sorting by time. Tasks that overlap another task get a ⚠️ in the table.
* Complete a task: a recurring task automatically queues its next occurrence.
* See conflict warnings: overlapping tasks are listed in one warning, each with a suggested free slot. The page shows a green "No scheduling conflicts" message when there are none.
* Generate a schedule: this builds today's plan from the most urgent tasks that fit in your available time. It also lists tasks skipped for overlapping a planned task, and tasks that didn't fit in the time.


Example workflow:
1. Enter your name and set 120 minutes available.
2. Add a pet, for example Mochi, a white dog.
3. Add a task: "Morning walk", 30 minutes, high priority, daily, starting at 9:00. Add "Vet check-up", 45 minutes, starting at 9:15.
4. In the task list, both tasks show a ⚠️. A warning says "Morning walk (09:00-09:30) overlaps Vet check-up (09:15-10:00) … Next free slot for 'Vet check-up': 09:30."
5. Fix it by adding the vet task again at 9:30, or just move on. Turn on "Sort by time" to see the day in order.
6. Click Generate schedule. The table shows the plan in priority order, and a message shows how many of your minutes it uses. The overlapping vet task is listed as skipped, with a suggested time.
7. Select "Morning walk" and click Complete task. Tomorrow's walk is added automatically.


Scheduler behaviors shown: 
* Sorting: tasks sort by start time, with untimed tasks last and ties broken by priority. The plan itself is ordered by priority, then deadline, then shortest duration.
* Filtering: by pet name (case-insensitive) and by completion status.
Conflict warnings: any two timed tasks whose time ranges overlap are flagged, for the same pet or different pets. Back-to-back tasks are fine. The check never crashes the page, even on bad time data.
* Recurring tasks: completing a daily or weekly task queues the next one from today's date, whether it was done early or late. Completing the same task twice doesn't create a duplicate.
* Time budget: the plan only includes tasks that fit in your available minutes. Tasks that don't fit are listed separately.


Sample CLI output" 
Added order (unsorted)
  [ ] 06:30 PM  Brush fur        Garfield   15 min  (priority 3)
  [x] 02:00 PM  Vet check-up     Sparky     45 min  (priority 2)
  [ ]   --     Buy cat food     Garfield   20 min  (priority 2)
  [ ] 07:30 AM  Morning walk     Sparky     30 min  (priority 1)
  [ ] 08:15 AM  Feed breakfast   Garfield   10 min  (priority 1)

Today's Schedule for Saniya (Wednesday, October 07) - sort_by_time()
  [ ] 07:30 AM  Morning walk     Sparky     30 min  (priority 1)
  [ ] 08:15 AM  Feed breakfast   Garfield   10 min  (priority 1)
  [x] 02:00 PM  Vet check-up     Sparky     45 min  (priority 2)
  [ ] 06:30 PM  Brush fur        Garfield   15 min  (priority 3)
  [ ]   --     Buy cat food     Garfield   20 min  (priority 2)

Sparky's tasks - filter_tasks(pet_name='sparky')
  [x] 02:00 PM  Vet check-up     Sparky     45 min  (priority 2)
  [ ] 07:30 AM  Morning walk     Sparky     30 min  (priority 1)

Garfield's pending tasks - filter_tasks(pet_name='Garfield', completed=False)
  [ ] 06:30 PM  Brush fur        Garfield   15 min  (priority 3)
  [ ]   --     Buy cat food     Garfield   20 min  (priority 2)
  [ ] 08:15 AM  Feed breakfast   Garfield   10 min  (priority 1)

Completed tasks - filter_tasks(completed=True)
  [x] 02:00 PM  Vet check-up     Sparky     45 min  (priority 2)

Unknown pet - filter_tasks(pet_name='Nobody')
  (none)

Conflict check - conflict_warnings()
  Warning: 'Morning walk' (07:30-08:00) overlaps 'Grooming' (07:30-08:00) for Sparky and Garfield. Next free slot for 'Grooming': 08:25.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

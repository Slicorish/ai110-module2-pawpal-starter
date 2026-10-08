from datetime import date, datetime, timedelta

import pytest

from pawpal_systems import Owner, Pet, Task


def make_pet() -> Pet:
    return Pet("Sparky", "dog", date(2021, 3, 14), 22.5, "M", "brown")


def test_complete_changes_task_status():
    """Completing a task flips its completed flag to True."""
    task = Task("Morning walk", 30, date.today(), 1, make_pet())
    assert task.completed is False

    task.complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Each task added through the owner shows up in that pet's task list."""
    pet = make_pet()
    owner = Owner("Saniya", pets=[pet])
    assert len(owner.tasks_for(pet)) == 0

    owner.add_task(Task("Morning walk", 30, date.today(), 1, pet))
    assert len(owner.tasks_for(pet)) == 1

    owner.add_task(Task("Vet check-up", 45, date.today(), 2, pet))
    assert len(owner.tasks_for(pet)) == 2


def at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(date.today(), datetime.min.time()).replace(hour=hour, minute=minute)


def make_owner(minutes: int = 120) -> tuple[Owner, Pet]:
    owner, pet = Owner("Jo", available_time=minutes), make_pet()
    owner.add_pet(pet)
    return owner, pet


def test_completing_twice_does_not_duplicate_recurring_task():
    """Completing a recurring task a second time queues nothing, so no duplicate next occurrence."""
    owner, pet = make_owner()
    task = Task("Feed", 5, date.today(), 1, pet, frequency="daily")
    owner.add_task(task)

    assert owner.schedule.complete_task(task) is not None
    assert owner.schedule.complete_task(task) is None
    assert len(owner.schedule.tasks) == 2


def test_late_recurring_task_reschedules_from_today():
    """A recurring task completed late is rescheduled from today (deadline and start time), not from its old date."""
    pet = make_pet()
    old = date.today() - timedelta(days=5)
    task = Task("Feed", 5, old, 1, pet, frequency="daily", start_time=at(8) - timedelta(days=5))

    nxt = task.complete()

    assert nxt.deadline == date.today() + timedelta(days=1)
    assert nxt.start_time == at(8) + timedelta(days=1)


def test_on_time_recurring_task_advances_one_period():
    """A weekly task completed on time is next due in 7 days."""
    task = Task("Bath", 20, date.today(), 2, make_pet(), frequency="weekly")
    assert task.complete().deadline == date.today() + timedelta(days=7)


def test_sort_by_time_puts_untimed_last_and_breaks_ties_by_priority():
    """sort_by_time puts untimed tasks last and orders same-start tasks by priority."""
    owner, pet = make_owner()
    untimed = Task("Untimed", 5, date.today(), 1, pet)
    late = Task("Late", 5, date.today(), 1, pet, start_time=at(15))
    low = Task("Low", 5, date.today(), 3, pet, start_time=at(9))
    high = Task("High", 5, date.today(), 1, pet, start_time=at(9))
    for t in (untimed, late, low, high):
        owner.add_task(t)

    assert owner.schedule.sort_by_time() == [high, low, late, untimed]


def test_fit_to_time_skips_overlapping_lower_priority_task():
    """A lower-priority task overlapping a planned one is dropped from the plan and reported as a conflict and as unscheduled."""
    owner, pet = make_owner()
    vet = Task("Vet", 60, date.today(), 1, pet, start_time=at(9))
    walk = Task("Walk", 30, date.today(), 2, pet, start_time=at(9, 30))
    owner.add_task(vet)
    owner.add_task(walk)

    assert owner.schedule.fit_to_time() == [vet]
    assert owner.schedule.conflicting_tasks() == [(walk, vet)]
    assert owner.schedule.unscheduled() == [walk]


def test_back_to_back_tasks_do_not_conflict():
    """Tasks where one ends exactly as the next starts do not conflict and both get planned."""
    owner, pet = make_owner()
    owner.add_task(Task("A", 30, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(Task("B", 30, date.today(), 1, pet, start_time=at(9, 30)))

    assert owner.schedule.find_conflicts() == []
    assert len(owner.schedule.fit_to_time()) == 2


def test_next_free_slot_skips_past_back_to_back_blocks():
    """next_free_slot jumps past a chain of adjacent tasks to the first open time."""
    owner, pet = make_owner()
    owner.add_task(Task("A", 60, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(Task("B", 30, date.today(), 1, pet, start_time=at(10)))

    assert owner.schedule.next_free_slot(15, at(9)) == at(10, 30)


def test_next_free_slot_uses_gap_and_ignores_excluded_task():
    """next_free_slot uses a gap only if the task fits, and ignores the excluded task (the one being moved)."""
    owner, pet = make_owner()
    a = Task("A", 30, date.today(), 1, pet, start_time=at(9))
    b = Task("B", 30, date.today(), 1, pet, start_time=at(11))
    owner.add_task(a)
    owner.add_task(b)

    assert owner.schedule.next_free_slot(60, at(9)) == at(9, 30)
    assert owner.schedule.next_free_slot(120, at(9)) == at(11, 30)
    assert owner.schedule.next_free_slot(30, at(9), exclude=a) == at(9)


def test_filter_tasks_by_pet_name_and_completion():
    """filter_tasks matches pet name case-insensitively, filters by completion, and returns [] for an unknown pet."""
    rex, mochi = make_pet(), Pet("Mochi", "cat", date(2020, 1, 1), 4.0, "F", "white")
    owner = Owner("Saniya", pets=[rex, mochi])
    walk = Task("Walk", 30, date.today(), 1, rex)
    feed = Task("Feed", 10, date.today(), 1, mochi)
    brush = Task("Brush", 15, date.today(), 2, mochi)
    for t in (walk, feed, brush):
        owner.add_task(t)
    brush.complete()

    sched = owner.schedule
    assert sched.filter_tasks(pet_name="mochi") == [feed, brush]
    assert sched.filter_tasks(pet_name="Mochi", completed=False) == [feed]
    assert sched.filter_tasks(completed=True) == [brush]
    assert sched.filter_tasks(pet_name="Nobody") == []


def test_early_completion_still_schedules_from_today():
    """Completing a daily or weekly task before its deadline still schedules the next one from today."""
    future = date.today() + timedelta(days=3)
    daily = Task("Feed", 5, future, 1, make_pet(), frequency="daily")
    assert daily.complete().deadline == date.today() + timedelta(days=1)
    weekly = Task("Bath", 20, future, 2, make_pet(), frequency="weekly")
    assert weekly.complete().deadline == date.today() + timedelta(days=7)


def test_complete_task_adds_next_occurrence_to_scheduler():
    """Scheduler.complete_task appends the new occurrence to the task list as a separate, incomplete task due tomorrow."""
    pet = make_pet()
    owner = Owner("Saniya", pets=[pet])
    task = Task("Feed", 5, date.today(), 1, pet, frequency="daily")
    owner.add_task(task)

    nxt = owner.schedule.complete_task(task)

    assert nxt in owner.schedule.tasks and nxt is not task
    assert nxt.completed is False
    assert nxt.deadline == date.today() + timedelta(days=1)
    assert len(owner.tasks_for(pet)) == 2


def test_conflict_warnings_same_pet_and_different_pets():
    """Overlaps produce one warning per pair, naming the pet for same-pet conflicts and both pets otherwise."""
    owner, pet = make_owner()
    cat = Pet("Mimi", "cat", date(2020, 1, 1), 4.0, "F", "white")
    owner.add_pet(cat)
    owner.add_task(Task("Walk", 30, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(Task("Vet", 30, date.today(), 1, pet, start_time=at(9, 15)))
    owner.add_task(Task("Groom", 30, date.today(), 1, cat, start_time=at(9, 20)))

    warnings = owner.schedule.conflict_warnings()

    assert len(warnings) == 3
    assert "for Sparky." in warnings[0]
    assert "for Sparky and Mimi." in warnings[1]


def test_conflict_warnings_empty_when_no_overlap():
    """Back-to-back tasks produce no warnings."""
    owner, pet = make_owner()
    owner.add_task(Task("A", 30, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(Task("B", 30, date.today(), 1, pet, start_time=at(9, 30)))

    assert owner.schedule.conflict_warnings() == []


def test_conflict_warnings_does_not_crash_on_bad_time_data():
    """Mixing naive and timezone-aware start times yields an 'invalid time data' warning instead of raising."""
    from datetime import timezone

    owner, pet = make_owner()
    owner.add_task(Task("A", 30, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(
        Task("B", 30, date.today(), 1, pet, start_time=at(9).replace(tzinfo=timezone.utc))
    )

    warnings = owner.schedule.conflict_warnings()

    assert len(warnings) == 1 and "invalid time data" in warnings[0]


def test_conflict_warning_suggests_next_free_slot():
    """A conflict warning ends with the next free slot for the second task."""
    owner, pet = make_owner()
    owner.add_task(Task("Walk", 60, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(Task("Vet", 30, date.today(), 1, pet, start_time=at(9, 30)))

    assert "Next free slot for 'Vet': 10:00." in owner.schedule.conflict_warnings()[0]


# ---------- Empty and missing data ----------


def test_pet_with_no_tasks_returns_empty_lists():
    """A pet with no tasks gets [] from both tasks_for and filter_tasks."""
    owner, pet = make_owner()
    other = Pet("Mimi", "cat", date(2020, 1, 1), 4.0, "F", "white")
    owner.add_pet(other)
    owner.add_task(Task("Walk", 30, date.today(), 1, pet))

    assert owner.tasks_for(other) == []
    assert owner.schedule.filter_tasks(pet=other) == []


def test_empty_scheduler_returns_empty_results():
    """With no tasks at all, every query method returns an empty list without error."""
    owner, _ = make_owner()
    s = owner.schedule

    assert s.sort_by_time() == []
    assert s.fit_to_time() == []
    assert s.unscheduled() == []
    assert s.find_conflicts() == []
    assert s.conflict_warnings() == []


def test_add_task_for_foreign_pet_raises():
    """Adding a task for a pet the owner doesn't have raises ValueError."""
    owner, _ = make_owner()
    stranger = Pet("Rex", "dog", date(2020, 1, 1), 10.0, "M", "black")

    with pytest.raises(ValueError):
        owner.add_task(Task("Walk", 30, date.today(), 1, stranger))


def test_zero_available_time_plans_nothing():
    """With zero available minutes nothing is planned and every task is unscheduled."""
    owner, pet = make_owner(minutes=0)
    task = Task("Walk", 30, date.today(), 1, pet)
    owner.add_task(task)

    assert owner.schedule.fit_to_time() == []
    assert owner.schedule.unscheduled() == [task]


# ---------- Happy paths ----------


def test_sort_by_time_orders_chronologically():
    """Tasks added out of order come back from sort_by_time earliest first."""
    owner, pet = make_owner()
    late = Task("Late", 5, date.today(), 1, pet, start_time=at(18))
    early = Task("Early", 5, date.today(), 1, pet, start_time=at(7))
    mid = Task("Mid", 5, date.today(), 1, pet, start_time=at(12))
    for t in (late, early, mid):
        owner.add_task(t)

    assert owner.schedule.sort_by_time() == [early, mid, late]


def test_fit_to_time_plans_everything_that_fits_most_urgent_first():
    """When everything fits, the plan includes all tasks in priority order and nothing is left out."""
    owner, pet = make_owner(minutes=100)
    low = Task("Low", 30, date.today(), 3, pet)
    high = Task("High", 30, date.today(), 1, pet)
    mid = Task("Mid", 30, date.today(), 2, pet)
    for t in (low, high, mid):
        owner.add_task(t)

    assert owner.schedule.fit_to_time() == [high, mid, low]
    assert owner.schedule.unscheduled() == []


def test_completing_one_off_task_queues_no_repeat():
    """Completing a one-off task marks it done and adds no new task."""
    owner, pet = make_owner()
    task = Task("Vet", 45, date.today(), 1, pet)
    owner.add_task(task)

    assert owner.schedule.complete_task(task) is None
    assert task.completed is True
    assert owner.schedule.tasks == [task]


# ---------- Sorting ties ----------


def test_identical_tasks_keep_their_original_order():
    """Fully tied tasks stay in insertion order in both sort_by_time and prioritize (stable sort)."""
    owner, pet = make_owner()
    a = Task("A", 10, date.today(), 2, pet, start_time=at(9))
    b = Task("B", 10, date.today(), 2, pet, start_time=at(9))
    c = Task("C", 10, date.today(), 2, pet, start_time=at(9))
    for t in (a, b, c):
        owner.add_task(t)

    assert owner.schedule.sort_by_time() == [a, b, c]
    owner.schedule.prioritize()
    assert owner.schedule.tasks == [a, b, c]


def test_prioritize_sinks_completed_tasks():
    """prioritize puts completed tasks after incomplete ones, even when the completed one has higher priority."""
    owner, pet = make_owner()
    done = Task("Done", 5, date.today(), 1, pet, completed=True)
    todo = Task("Todo", 5, date.today(), 3, pet)
    owner.add_task(done)
    owner.add_task(todo)

    owner.schedule.prioritize()

    assert owner.schedule.tasks == [todo, done]


# ---------- Conflicts ----------


def test_exact_same_start_time_conflicts_for_same_pet():
    """Two tasks for one pet starting at the same moment are flagged as a conflict."""
    owner, pet = make_owner()
    owner.add_task(Task("A", 30, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(Task("B", 30, date.today(), 1, pet, start_time=at(9)))

    assert len(owner.schedule.find_conflicts()) == 1
    assert len(owner.schedule.conflict_warnings()) == 1


def test_task_fully_inside_another_conflicts():
    """A short task that sits entirely inside a long one is a conflict."""
    owner, pet = make_owner()
    owner.add_task(Task("Long", 120, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(Task("Short", 15, date.today(), 1, pet, start_time=at(10)))

    assert len(owner.schedule.find_conflicts()) == 1


def test_completed_task_does_not_conflict():
    """A completed task is ignored by conflict detection."""
    owner, pet = make_owner()
    owner.add_task(Task("Done", 30, date.today(), 1, pet, start_time=at(9), completed=True))
    owner.add_task(Task("Todo", 30, date.today(), 1, pet, start_time=at(9)))

    assert owner.schedule.find_conflicts() == []
    assert owner.schedule.conflict_warnings() == []


def test_three_overlapping_tasks_give_three_pairs():
    """Three mutually overlapping tasks yield exactly three pairs, none missed or duplicated."""
    owner, pet = make_owner()
    for name in "ABC":
        owner.add_task(Task(name, 60, date.today(), 1, pet, start_time=at(9)))

    assert len(owner.schedule.find_conflicts()) == 3
    assert len(owner.schedule.conflict_warnings()) == 3


def test_untimed_task_never_conflicts():
    """A task without a start time can't conflict with a timed one."""
    owner, pet = make_owner()
    owner.add_task(Task("Timed", 60, date.today(), 1, pet, start_time=at(9)))
    owner.add_task(Task("Untimed", 60, date.today(), 1, pet))

    assert owner.schedule.find_conflicts() == []


# ---------- Recurring tasks ----------


def test_recurring_task_without_start_time_repeats_untimed():
    """A recurring task with no start time repeats with no start time."""
    task = Task("Feed", 5, date.today(), 1, make_pet(), frequency="daily")

    nxt = task.complete()

    assert nxt.start_time is None
    assert nxt.deadline == date.today() + timedelta(days=1)


def test_unknown_frequency_raises():
    """A frequency other than once, daily or weekly raises ValueError."""
    with pytest.raises(ValueError):
        Task("Bath", 20, date.today(), 1, make_pet(), frequency="monthly")


# ---------- Planning ----------


def test_task_exactly_equal_to_remaining_time_fits():
    """A task whose duration equals the minutes left still fits (the check is > not >=)."""
    owner, pet = make_owner(minutes=60)
    owner.add_task(Task("A", 30, date.today(), 1, pet))
    owner.add_task(Task("B", 30, date.today(), 2, pet))

    assert len(owner.schedule.fit_to_time()) == 2


def test_task_longer_than_budget_is_unscheduled_but_not_a_conflict():
    """A task longer than the time budget is unscheduled but not reported as a conflict."""
    owner, pet = make_owner(minutes=30)
    big = Task("Big", 60, date.today(), 1, pet, start_time=at(9))
    owner.add_task(big)

    assert owner.schedule.fit_to_time() == []
    assert owner.schedule.unscheduled() == [big]
    assert owner.schedule.conflicting_tasks() == []


def test_next_free_slot_after_all_tasks_returns_requested_time():
    """If the requested time is after every task, it is returned unchanged."""
    owner, pet = make_owner()
    owner.add_task(Task("A", 30, date.today(), 1, pet, start_time=at(9)))

    assert owner.schedule.next_free_slot(30, at(15)) == at(15)


def test_task_spanning_midnight_ends_next_day_and_conflicts_there():
    """A task running past midnight ends on the next day and conflicts with a task early that day."""
    owner, pet = make_owner()
    night = Task("Night", 60, date.today(), 1, pet, start_time=at(23, 30))
    early = Task("Early", 30, date.today(), 1, pet, start_time=at(0) + timedelta(days=1))
    owner.add_task(night)
    owner.add_task(early)

    assert night.end_time == at(0, 30) + timedelta(days=1)
    assert owner.schedule.find_conflicts() == [(night, early)]

from datetime import date

from pawpal_systems import Owner, Pet, Task


def make_pet() -> Pet:
    return Pet("Sparky", "dog", date(2021, 3, 14), 22.5, "M", "brown")


def test_complete_changes_task_status():
    task = Task("Morning walk", 30, date.today(), 1, make_pet())
    assert task.completed is False

    task.complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = make_pet()
    owner = Owner("Saniya", pets=[pet])
    assert len(owner.tasks_for(pet)) == 0

    owner.add_task(Task("Morning walk", 30, date.today(), 1, pet))
    assert len(owner.tasks_for(pet)) == 1

    owner.add_task(Task("Vet check-up", 45, date.today(), 2, pet))
    assert len(owner.tasks_for(pet)) == 2

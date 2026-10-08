# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

* Three core actions a user should be able to perform
    - create a pet
    - feed the pet
    - create todo list for the pet

* Main objects, their attributes, and their methods
    1. Pet: attributes --> name, age, birthday, weight, gender, color ; methods --> eat, walk, bark, sleep, play
    2. Food: attributes --> type (dry or wet food), serving_size ; methods --> purchase, feed
    3. Todo_List: attributes --> task ; methods --> remove, print, add, prioritize
    4. Task: attributes --> description, duration, deadline, priority ; methods: create, delete,complete
    5. Owner: attributes --> name, schedule for the day ; methods: create schedule, edit schedule

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
    1. Design did change during implementation: schedule was combined with todolist, with the current logic it was an attribute that wasn't connected to an object outside of owner, as in there was not relationship with it, so it was just combined
    2. A species attribute was added to pet, this will add more functionality for polymorphism and encapsulation if needed later down the road
    3. My AI chat found and fixed the following relationship gaps: Task to pet link: Task now has pet: Pet | None = None; Food to pet link: Food.feed(self, pet: Pet) now takes the pet it feeds; Completion state: Task.completed: bool = False, which complete() can set later; Food stock: Food.quantity: int = 0, which purchase() and feed() can update; Owner's schedule now owns ass tasks, and it's still a TodoList; todolist.add and todolist.remove were removed due to overlapping functionality with edit_schedule
    4. My AI found the following logic bottlenecks: age and birthday are redundant, they will drift out of sync you can calculate age from birthday; task.create and task.delete don't fit a dataclass; prioritize() needs a rule/logic; todolist.print() shadows built-in print, a method named display is safer to implement; owner.create_schedule and edit_schedule() overlap with TodoList. If schedule is a TodoList, then add() and remove() already do the same thing; Time-dependent scheduling has no support yet; bark() only applies to one specific species/type of pet


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff is that fit_to_time() in pawpal_systems.py builds the plan greedily, in priority order, meaning it never searches for the best combination. It goes through the tasks from most to least urgent and keeps each one that still fits in the remaining time and doesn't overlap something already planned. This makes the algorithm logic simple, fast and predictable. Urgent tasks always win, and it's easy to explain why a task was skipped. The downside is that it can produce a worse plan than one that looks at all the tasks together. For example, with 60 minutes available, The same thing happens with overlaps: a high-priority task that sits across two lower-priority ones blocks both, even if those two together matter more. A priority 1 task takes 45 minutes.Two priority 2 tasks take 30 minutes each.
The greedy plan books the 45-minute task, and neither 30-minute task fits in the remaining 15. That's one task for 45 minutes, when the two 30-minute tasks could have used all 60. 


---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

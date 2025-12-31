import random
from collections import defaultdict

def initialize_population(courses, faculties, rooms, DAYS, TIME_SLOTS, POPULATION_SIZE):
    population = []
    for _ in range(POPULATION_SIZE):
        schedule = []
        
        # Tracking structures
        room_slots = {r["name"]: {day: {slot: None for slot in TIME_SLOTS} for day in DAYS} for r in rooms}
        faculty_slots = {f["id"]: {day: {slot: None for slot in TIME_SLOTS} for day in DAYS} for f in faculties}
        course_counts = {c["code"]: 0 for c in courses}
        
        # Schedule core courses first (most constrained)
        sorted_courses = sorted(courses, key=lambda x: (
            0 if x["type"] == "Core" else 
            1 if x["type"] == "Program-Specific" else 2
        ))
        
        for course in sorted_courses:
            remaining_hours = course["hours"]
            faculty_options = [f for f in faculties if course["code"] in f["courses"]]
            
            if not faculty_options:
                continue
                
            while remaining_hours > 0:
                faculty = random.choice(faculty_options)
                placed = False
                
                # Try to place in random slot
                for _ in range(50):  # Max attempts
                    day = random.choice(DAYS)
                    slot = random.choice(TIME_SLOTS)
                    
                    # Check faculty availability
                    if faculty_slots[faculty["id"]][day][slot] is not None:
                        continue
                        
                    # Check faculty daily limit
                    daily_count = sum(1 for s in faculty_slots[faculty["id"]][day].values() if s is not None)
                    if daily_count >= faculty["max_daily"]:
                        continue
                    
                    # Find suitable room
                    suitable_rooms = [
                        r for r in rooms 
                        if (r["type"] == course["room_type"] or 
                            (course["room_type"] == "Regular" and r["type"] != "Lab")) and
                        room_slots[r["name"]][day][slot] is None
                    ]
                    
                    if not suitable_rooms:
                        continue
                        
                    room = random.choice(suitable_rooms)
                    
                    # Create class group based on course type
                    if course["type"] == "Core":
                        class_group = f"{course['code']} (ALL)"
                    elif course["type"] == "Program-Specific":
                        class_group = f"{course['code']} ({'/'.join(course['target'])})"
                    else:  # Level-Specific
                        class_group = f"{course['code']} (L{'/'.join(course['target'])})"
                    
                    # Assign the class
                    room_slots[room["name"]][day][slot] = {
                        "course": course["code"],
                        "faculty": faculty["id"],
                        "class_group": class_group
                    }
                    
                    faculty_slots[faculty["id"]][day][slot] = {
                        "course": course["code"],
                        "room": room["name"]
                    }
                    
                    schedule.append({
                        "room": room["name"],
                        "day": day,
                        "time": slot,
                        "course": course["code"],
                        "faculty": faculty["id"],
                        "class_group": class_group
                    })
                    
                    course_counts[course["code"]] += 1
                    remaining_hours -= 1
                    placed = True
                    break
                
                if not placed:
                    break  # Couldn't place this hour
                    
        population.append(schedule)
    return population

def fitness(schedule, courses, faculties, rooms, DAYS, FACULTY_MIN_HOURS, FACULTY_MAX_HOURS):
    score = 0
    constraints = defaultdict(int)
    
    # Track metrics
    faculty_hours = {f["id"]: 0 for f in faculties}
    course_hours = {c["code"]: 0 for c in courses}
    room_usage = {r["name"]: 0 for r in rooms}
    faculty_daily = {f["id"]: {day: 0 for day in DAYS} for f in faculties}
    
    for entry in schedule:
        faculty_hours[entry["faculty"]] += 1
        course_hours[entry["course"]] += 1
        room_usage[entry["room"]] += 1
        faculty_daily[entry["faculty"]][entry["day"]] += 1
    
    # 1. Faculty workload constraints
    for fid, hours in faculty_hours.items():
        if FACULTY_MIN_HOURS <= hours <= FACULTY_MAX_HOURS:
            score += 20
        else:
            score -= abs(hours - (FACULTY_MIN_HOURS + FACULTY_MAX_HOURS)/2) * 2
    
    # 2. Course hours fulfillment
    for c in courses:
        fulfilled = course_hours.get(c["code"], 0)
        if fulfilled == c["hours"]:
            score += 15
        else:
            score -= abs(fulfilled - c["hours"]) * 3
    
    # 3. Faculty daily limits
    for fid, daily_counts in faculty_daily.items():
        max_daily = next(f["max_daily"] for f in faculties if f["id"] == fid)
        for day, count in daily_counts.items():
            if count > max_daily:
                score -= (count - max_daily) * 5
    
    # 4. Room suitability
    for entry in schedule:
        course = next(c for c in courses if c["code"] == entry["course"])
        room = next(r for r in rooms if r["name"] == entry["room"])
        if course["room_type"] == "Lab" and room["type"] != "Lab":
            score -= 10
        elif course["room_type"] == "Regular" and room["type"] == "Lab":
            score -= 5
    
    return score

def mutate(schedule, DAYS, TIME_SLOTS, MUTATION_RATE):
    if random.random() < MUTATION_RATE and len(schedule) > 1:
        # Mutation 1: Swap two classes
        idx1, idx2 = random.sample(range(len(schedule)), 2)
        schedule[idx1], schedule[idx2] = schedule[idx2], schedule[idx1]
        
        # Mutation 2: Randomly reschedule a class
        if random.random() < 0.3:
            idx = random.randint(0, len(schedule)-1)
            entry = schedule[idx]
            
            # Find new slot
            for _ in range(20):
                new_day = random.choice(DAYS)
                new_slot = random.choice(TIME_SLOTS)
                
                # Check if faculty and room are available
                faculty_free = all(
                    e["day"] != new_day or e["time"] != new_slot or e["faculty"] != entry["faculty"]
                    for e in schedule if e != entry
                )
                
                room_free = all(
                    e["day"] != new_day or e["time"] != new_slot or e["room"] != entry["room"]
                    for e in schedule if e != entry
                )
                
                if faculty_free and room_free:
                    schedule[idx]["day"] = new_day
                    schedule[idx]["time"] = new_slot
                    break
    
    return schedule

def crossover(parent1, parent2):
    # Uniform crossover
    child = []
    p1_dict = {(e["room"], e["day"], e["time"]): e for e in parent1}
    p2_dict = {(e["room"], e["day"], e["time"]): e for e in parent2}
    
    # Take slots from either parent
    all_slots = set(p1_dict.keys()).union(set(p2_dict.keys()))
    
    for slot in all_slots:
        if slot in p1_dict and slot in p2_dict:
            # Choose randomly from parents
            child.append(random.choice([p1_dict[slot], p2_dict[slot]]))
        elif slot in p1_dict:
            if random.random() < 0.7:  # Bias toward keeping existing assignments
                child.append(p1_dict[slot])
        elif slot in p2_dict:
            if random.random() < 0.7:
                child.append(p2_dict[slot])
    
    return child

def generate_timetable(courses, faculties, rooms, DAYS, TIME_SLOTS, POPULATION_SIZE, GENERATIONS, MUTATION_RATE, FACULTY_MIN_HOURS, FACULTY_MAX_HOURS):
    population = initialize_population(courses, faculties, rooms, DAYS, TIME_SLOTS, POPULATION_SIZE)
    
    for generation in range(GENERATIONS):
        # Evaluate and sort
        population = sorted(
            population,
            key=lambda x: fitness(x, courses, faculties, rooms, DAYS, FACULTY_MIN_HOURS, FACULTY_MAX_HOURS),
            reverse=True
        )
        
        # Keep top performers
        elite_size = POPULATION_SIZE // 5
        elites = population[:elite_size]
        
        # Breed new generation
        new_population = elites.copy()
        
        while len(new_population) < POPULATION_SIZE:
            # Tournament selection
            parents = random.sample(elites, min(2, len(elites)))
            offspring = crossover(parents[0], parents[1])
            offspring = mutate(offspring, DAYS, TIME_SLOTS, MUTATION_RATE)
            new_population.append(offspring)
        
        population = new_population
    
    return max(
        population,
        key=lambda x: fitness(x, courses, faculties, rooms, DAYS, FACULTY_MIN_HOURS, FACULTY_MAX_HOURS)
    ) 
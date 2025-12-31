# Time slots and days constants
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["08:00-10:00", "10:00-12:00", "12:00-14:00", "14:00-16:00"]

# Weekly module requirements
WEEKLY_MODULE_HOURS = 4  # Exactly 4 hours (two sessions) per module each week
SESSIONS_PER_MODULE = WEEKLY_MODULE_HOURS // 2

# Module constraints
MODULE_MAX_DAILY_HOURS = 2  # Max 2 hours/day (1 session)
MODULE_MAX_WEEKLY_HOURS = WEEKLY_MODULE_HOURS  # Exactly 4 hours/week
MODULE_MIN_WEEKLY_HOURS = WEEKLY_MODULE_HOURS  # Exactly 4 hours/week

# Faculty constraints
FACULTY_MIN_HOURS = 4       # Minimum weekly teaching hours per lecturer
MIN_FACULTY_HOURS = 4
FACULTY_MAX_HOURS = 20      # Maximum weekly teaching hours (10 sessions × 2 hours)
MAX_FACULTY_HOURS = 20
FACULTY_DAILY_MAX_HOURS = 4  # Maximum daily teaching hours (2 sessions)

# Room constraints
MAX_ROOM_CAPACITY = 5      # Maximum number of modules that can share a room slot
MIN_ROOM_CAPACITY = 1       # Minimum capacity for room assignment

# Tandem scheduling constants
TANDEM_SLOTS = {
    "08:00-10:00": "10:00-12:00",  
    "10:00-12:00": "12:00-14:00",
    "12:00-14:00": "14:00-16:00"
}

# Genetic Algorithm Parameters - Optimized for performance
POPULATION_SIZE = 200  # Reduced from 500 for faster execution
GENERATIONS = 1000     # Reduced from 5000 for faster convergence
INITIAL_MUTATION_RATE = 0.15  # Slightly increased for better exploration
TOURNAMENT_SIZE = 5            # Increased for better selection pressure
ELITISM_COUNT = 5               # Increased to preserve more top solutions

# Parallel processing
import multiprocessing
NUM_PARALLEL_PROCESSES = max(1, multiprocessing.cpu_count() - 1)  
MAX_ATTEMPTS = 200              # Maximum attempts for scheduling a module

# Early stopping parameters
EARLY_STOPPING_GENERATIONS = 100
MIN_IMPROVEMENT = 0.001

# Room allocation strategies
ROOM_ALLOCATION_STRATEGIES = ['balanced', 'capacity_first', 'largest_first', 'smallest_first']

# Performance optimization
ENABLE_PARALLEL_PROCESSING = True  # Enable/disable parallel processing
CACHE_FITNESS_VALUES = True        # Cache fitness values for better performance
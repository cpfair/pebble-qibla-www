from models import User
from timeline import Timeline
from threading import Event, Lock

# Normally this creates all futures up front
# ...which soaks up a lot of RAM
# So, instead, we create this many initially, and chain new futures off completion callbacks
max_outstanding_futures = 100

future_generator_lock = Lock()
exhausted_future_generator = Event()

user_count = 0
successful_pin_count = 0
failed_pin_count = 0

def pin_future_generator():
    global user_count
    for user in User.objects(timeline_token__exists=True):
        user_count += 1
        yield from Timeline.push_pins_for_user(user)

def pin_future_done(future):
    global successful_pin_count, failed_pin_count, outstanding_futures
    exc = future.exception()
    if exc:
        failed_pin_count += 1
        print(exc)
    else:
        successful_pin_count += 1

    # Start another future, if any are available
    try:
        with future_generator_lock:
            future = next(pin_iter)
        future.add_done_callback(pin_future_done)
    except StopIteration:
        exhausted_future_generator.set()

pin_iter = pin_future_generator()

try:
    for x in range(max_outstanding_futures):
        with future_generator_lock:
            future = next(pin_iter)
        future.add_done_callback(pin_future_done)
except StopIteration:
    exhausted_future_generator.set()

exhausted_future_generator.wait()
Timeline.executor.shutdown()

print("%d pins pushed, %d failed for %d users" % (successful_pin_count, failed_pin_count, user_count))

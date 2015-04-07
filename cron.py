from models import User
from timeline import Timeline
import concurrent.futures

pending_pins = []
user_count = 0
for user in User.objects:
    user_count += 1
    pending_pins += Timeline.push_pins_for_user(user)

print("Dispatched %d pins for %d users" % (len(pending_pins), user_count))

concurrent.futures.wait(pending_pins)
ok = set([x for x in pending_pins if not x.exception()])
failed = set(pending_pins) - ok

print("%d pins pushed, %d failed" % (len(ok), len(failed)))
for failed_pin in failed:
    print(failed_pin.exception())

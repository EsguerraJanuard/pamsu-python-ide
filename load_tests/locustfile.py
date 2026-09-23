import os
import gevent.lock
from locust import HttpUser, task, between

_login_lock = gevent.lock.Semaphore()
_global_token = None

class StudentUser(HttpUser):
    # Simulate the think-time between student actions (1 to 5 seconds)
    wait_time = between(1, 5)

    def on_start(self):
        """
        Called when a simulated user starts.
        """
        global _global_token
        self.username = "student@pampangastateu.edu.ph"
        self.password = "Password123!"
        
        if not _global_token:
            with _login_lock:
                if not _global_token:
                    # Retry login up to 3 times to survive DB pool spikes
                    import time
                    for attempt in range(3):
                        response = self.client.post("/login", data={
                            "username": self.username,
                            "password": self.password,
                        })
                        if response.status_code == 200:
                            _global_token = response.json().get("access_token")
                            break
                        else:
                            print(f"Login failed (attempt {attempt+1}): {response.text}")
                            time.sleep(2)
                
        self.token = _global_token
        if not self.token:
            from locust.exception import StopUser
            raise StopUser()
            
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(3)
    def fetch_classes(self):
        """
        Simulate a student landing on their dashboard,
        fetching their enrolled classrooms.
        """
        if not self.token: return
        
        self.client.get("/classrooms/mine", name="/classrooms/mine")

    @task(1)
    def fetch_activities(self):
        """
        Simulate fetching classroom activities.
        (Requires a valid classroom, this tests error handling/404s if none exist)
        """
        if not self.token: return
        
        with self.client.get("/activities/1", catch_response=True, name="/activities/{id}") as response:
            if response.status_code in [200, 404, 403]:
                response.success()

    @task(2)
    def run_code_execution(self):
        """
        Simulates a student hitting the 'Run Code' button.
        This tests the database, Redis Celery broker, Celery worker, and Judge0 cluster!
        """
        if not self.token: return
        
        # A realistic algorithm task: finding prime numbers
        source_code = """
def find_primes(limit):
    primes = []
    for num in range(2, limit + 1):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
    return primes

print(f"Found {len(find_primes(10000))} primes up to 10,000!")
"""

        payload = {
            "request_kind": "run",
            "task_id": 1, 
            "source_code": source_code
        }
        
        # Dispatch the execution request (Asynchronous)
        with self.client.post("/execution/requests/", json=payload, catch_response=True, name="POST /execution/requests") as response:
            if response.status_code == 201:
                exec_data = response.json()
                exec_id = exec_data.get("execution_id")
                
                # We'll do a quick polling simulation. Wait 1.5 seconds, then poll the result.
                if exec_id:
                    import gevent
                    gevent.sleep(1.5)
                    self.client.get(f"/execution/requests/{exec_id}", name="GET /execution/requests/{id}")
            elif response.status_code in [404, 403, 400]:
                response.success()


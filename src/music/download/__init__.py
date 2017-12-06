import threading

downloadMutex = threading.Semaphore(1)
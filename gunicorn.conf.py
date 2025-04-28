# Gunicorn configuration file

bind = "0.0.0.0:5000"
workers = 1
threads = 1
timeout = 600
keepalive = 5
preload_app = True
worker_class = "gthread"

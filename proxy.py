import socket, os, threading
def fwd(a, b):
    try:
        while True:
            d = a.recv(8192)
            if not d: break
            b.sendall(d)
    except: pass
    finally: a.close(); b.close()

if os.path.exists("/tmp/ai.sock"): os.remove("/tmp/ai.sock")
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.bind("/tmp/ai.sock")
s.listen(5)
os.chmod("/tmp/ai.sock", 0o777)
print("Bridge OPEN. Waiting for prompts...")
while True:
    c, _ = s.accept()
    r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r.connect(("127.0.0.1", 8080))
    threading.Thread(target=fwd, args=(c,r)).start()
    threading.Thread(target=fwd, args=(r,c)).start()

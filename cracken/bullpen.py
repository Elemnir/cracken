"""
    cracken.bullpen
    ~~~~~~~~~~~~~~~

    This module provides the Bullpen class, which starts and manages workers on
    remote hosts to run commands, as well as the Bullpen's workers
"""
from multiprocessing.managers   import BaseManager
from os                         import getenv, path
from Queue                      import Queue
from string                     import ascii_letters

import pydoc
import random
import shlex
import socket
import subprocess
import sys
import tempfile
import time

class BullpenManager(BaseManager):
    pass

class Bullpen(object):
    """The Bullpen starts and manages workers using the multiprocessing 
    library's manager class as the transport layer"""
    
    # Instantiated when an instance is instantiated
    _authkey = None
    _server  = None
    _started = False
    _rand_str_history = []
    _instances = []
    
    def __init__(self, hosts, target, host='0.0.0.0', port=8000, cwd=None, 
            user=None, id_file=None, venv=None):
        
        # Prevent instantiation after starting the server and instantiate the 
        # server with the first instance
        if (self._started):
            raise RuntimeError("Server started, can't make new Bullpens.")
        if (self._authkey == None):
            self._instantiate_server(host, port)

        # Generate a unique identifier for this instance's, queues create the
        # queues, and register them with the BullpenManager
        self.queue_id         = self._gen_unique_random_string(8)
        self._task_queue_inst = Queue()
        self._res_queue_inst  = Queue()
        BullpenManager.register("get_t{}".format(self.queue_id), 
            callable=lambda:self._task_queue_inst)
        BullpenManager.register("get_r{}".format(self.queue_id),
            callable=lambda:self._res_queue_inst)

        # Write the ssh command
        self.ssh_cmd = "/usr/bin/ssh -oStrictHostKeyChecking=no "
        if id_file:
            self.ssh_cmd += "-i {} ".format(id_file)
        if user:
            self.ssh_cmd += "{}@".format(user)
        self.ssh_cmd += "{} '/bin/bash -s'"

        # Write the worker script to be executed on the remote hosts
        self.hosts = hosts
        self.running_workers = 0
        self.script_cmd = ""
        if cwd:
            self.script_cmd += "cd {};\n".format(cwd)
        else:
            self.script_cmd += "cd {};\n".format(path.abspath('.'))

        if venv:
            self.script_cmd += "source {};\n".format(
                path.join(venv, "bin", "activate")
            )
        self.script_cmd += "export BULLPEN_AUTHKEY={}\n".format(self._authkey)
        self.script_cmd += ("nohup python -c \"" 
            + "from cracken.bullpen import run_worker; "
            + "run_worker('{}','{}','{}','{}');\" &\n"
            + "exit\n"
        ).format(target, socket.getfqdn(), port, self.queue_id)
       
        # Add this instance to the list of instances for launch_workers
        self._instances.append(self)
    

    def _start(self):
        """Start the Bullpen's workers via ssh and a shell script piped through
        a temporary file. Also grab the Bullpen's task and result queues from 
        the Manager server."""
        self._task_queue = getattr(self._server, "get_t{}".format(self.queue_id))()
        self._res_queue  = getattr(self._server, "get_r{}".format(self.queue_id))()

        for host in self.hosts:
            with tempfile.TemporaryFile() as f:
                f.write(self.script_cmd)
                f.seek(0)
                child = subprocess.Popen(
                    shlex.split(self.ssh_cmd.format(host)),
                    stdin=f,
                )


    @classmethod
    def _instantiate_server(cls, host, port):
        """Do the basic setup for the BullpenManager server, called when 
        initializing the first Bullpen."""
        if (cls._authkey != None):
            raise RuntimeError("Server can only be instantiated once.")
        cls._authkey = cls._gen_unique_random_string(64)
        cls._server  = BullpenManager(address=(host,port), authkey=cls._authkey) 


    @classmethod
    def _gen_unique_random_string(cls, length):
        """Generate a `length` character string guaranteed to be unique for this 
        instantiation of the Bullpen class"""
        s = ''.join(random.choice(ascii_letters) for i in range(length))
        while s in cls._rand_str_history:   
            s = ''.join(random.choice(ascii_letters) for i in range(length))
        cls._rand_str_history.append(s)
        return s


    @classmethod
    def launch_workers(cls):
        """Start the server, and then start all the Bullpens' workers"""
        if cls._started:
            raise RuntimeError("Server already started.")
        cls._server.start()
        for inst in cls._instances:
            inst._start()
        cls._started = True


    def enqueue(self, *args, **kwargs):
        """Pass the arguments and keyword arguments as a task, all arguments 
        must be pickle-able."""
        self._task_queue.put(("TASK", args, kwargs))


    def get_result(self):
        """Return a result from the result queue, prints any status messages sent 
        by workers, and blocks until a result is available"""
        mtype, res = self._res_queue.get()
        while mtype != "RESULT":
            if mtype == "STATUS":
                if "started" in res:
                    self.running_workers += 1
                if "TERM" in res:
                    self.running_workers -= 1

                sys.stdout.write("{}\n".format(res))
            mtype, res = self._res_queue.get()
        
        return res
    

    def kill_workers(self):
        """Flood the task queue with Terminate control messages. Workers will 
        terminate after completing their current task."""
        for host in self.hosts:
            self._task_queue.put(("TERM",))

    
    def join(self):
        while self.running_workers > 0:
            time.sleep(1)


def run_worker(modpath, host, port, queue_id):
    """Execute queued tasks using the provided worker function.
    
    This funtion will be invoked by the related Bullpen object when it ssh's 
    into the worker host. It wraps the worker function to connect and provide 
    access to the Bullpen's task and result queues.
    """
    # Connect to the Manager Server
    authkey = getenv("BULLPEN_AUTHKEY")
    man = BullpenManager(address=(host, int(port)), authkey=authkey)
    man.connect()
    
    # Load the task and result queues, as well as the worker callable
    worker = pydoc.locate(modpath)
    BullpenManager.register("get_t{}".format(queue_id))
    BullpenManager.register("get_r{}".format(queue_id))
    task_queue = getattr(man, "get_t{}".format(queue_id))()
    res_queue  = getattr(man, "get_r{}".format(queue_id))()

    # Report successful startup
    res_queue.put(("STATUS",
        "{}: worker started.".format(socket.getfqdn())
    ))
        
    # Run the event loop
    while True:
        task = task_queue.get()
        if task[0] == "TASK":
            args, kwargs = task[1:]
            res = worker(*args, **kwargs)
            if res != None:
                res_queue.put(("RESULT", res))
        if task[0] == "TERM":
            res_queue.put(("STATUS", "Got TERM task. Terminating."))
            break
